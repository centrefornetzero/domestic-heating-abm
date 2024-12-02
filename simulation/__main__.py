import argparse
import datetime
import os
import random
import sys
import uuid
import json
from functools import partial

import pandas as pd
import smart_open
import structlog
from dateutil.relativedelta import relativedelta

from abm import write_jsonlines
from simulation.constants import ENGLAND_WALES_ANNUAL_NEW_BUILDS, InterventionType
from simulation.model import create_and_run_simulation

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


def parse_args(args=None):
    def convert_to_datetime(date_string):
        return datetime.datetime.strptime(date_string, "%Y-%m-%d")

    def convert_to_months_relativedelta(months_string):
        return relativedelta(months=int(months_string))

    def float_between_0_and_1(value: str):
        if 0 <= float(value) <= 1:
            return float(value)
        raise ValueError(f"Value must be between 0 and 1, got {value}")

    def map_string_to_intervention_type_enum(intervention):
        return InterventionType[intervention.upper()]

    def map_string_to_datetime_float_tuple(date_price_discount_string):
        date, price_discount = date_price_discount_string.split(":")
        return datetime.datetime.strptime(date, "%Y-%m-%d"), float(price_discount)

    def map_string_to_datetime_float_dict(date_target_awareness_string):
        date_target_awareness = json.loads(date_target_awareness_string)
        date_target_awareness_dict = {}
        for date, awareness in date_target_awareness.items():
            date_target_awareness_dict[float(awareness)] = datetime.datetime.strptime(date, "%Y-%m-%d")
        return date_target_awareness_dict

    parser = argparse.ArgumentParser()

    households = parser.add_mutually_exclusive_group(required=True)
    households.add_argument("households", type=pd.read_parquet, nargs="?")
    households.add_argument(
        "--bigquery",
        help="Generate household agents from BigQuery result.",
        type=partial(
            pd.read_gbq, project_id=os.getenv("PROJECT_ID"), use_bqstorage_api=True
        ),
    )

    def format_uuid(str):
        return str.format(uuid=uuid.uuid4())

    parser.add_argument(
        "history_file",
        type=format_uuid,
        help="Local file or Google Cloud Storage URI. Suffix with .gz for compression. Add {uuid} for random ID.",
    )

    parser.add_argument(
        "--start-date",
        dest="start_datetime",
        type=convert_to_datetime,
        default=datetime.datetime(2024, 1, 1),
    )

    parser.add_argument(
        "--step-interval",
        type=convert_to_months_relativedelta,
        default=relativedelta(months=1),
        metavar="MONTHS",
    )

    parser.add_argument("--steps", dest="time_steps", type=int, default=156)
    parser.add_argument("--heat-pump-awareness", type=float, default=0.25)
    parser.add_argument("--annual-renovation-rate", type=float, default=0.1)
    parser.add_argument(
        "--household-num-lookahead-years",
        type=int,
        default=3,
        help="The number of years households look ahead when making purchasing decisions; any cash flows to be exchanged further than this number of years in the future are valued at £0 by households",
    )

    parser.add_argument(
        "--heating-system-hassle-factor",
        type=float_between_0_and_1,
        default=0.1,
        help="A value between 0 and 1 which suppresses the likelihood of a household choosing a given heating system (the higher the value, the lower the likelihood)",
    )

    parser.add_argument(
        "--rented-heating-system-hassle-factor",
        type=float_between_0_and_1,
        default=0.4,
        help="A value between 0 and 1 which suppresses the likelihood of a household choosing a given heating system (the higher the value, the lower the likelihood)",
    )

    parser.add_argument(
        "--intervention",
        action="append",
        help="Valid interventions are: "
        + ", ".join(member.name for member in InterventionType),
        type=map_string_to_intervention_type_enum,
    )

    parser.add_argument(
        "--all-agents-heat-pump-suitable",
        action="store_true",
        help="Make all households suitable for heat pumps.",
    )

    parser.add_argument(
        "--air-source-heat-pump-price-discount-date",
        action="append",
        type=map_string_to_datetime_float_tuple,
        help="A factor by which heat pump prices will fall by a specified date.",
        metavar="YYYY-MM-DD:price_discount",
    )

    parser.add_argument(
        "--heat-pump-installer-count",
        type=float,
        default=10_800,
        help="The number of HP installers at the start of the simulation.",
    )

    parser.add_argument(
        "--heat-pump-installer-annual-growth-rate",
        type=float,
        default=0.48,
        help="The YoY growth rate of heat pump installers across the simulation. A value of 0 indicates no growth.",
    )

    parser.add_argument(
        "--include-new-builds",
        action="store_true",
        help="Include new build projections (from constants.py). Installers will also build heat pumps in new builds from 2025.",
    )

    def check_string_is_isoformat_datetime(string) -> str:
        datetime.datetime.fromisoformat(string)
        return string

    parser.add_argument(
        "--seed",
        default=datetime.datetime.now().isoformat(),
        type=check_string_is_isoformat_datetime,
        help="""
        Seed for random number generator. Default is now.
    """,
        metavar="YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]]",
    )

    parser.add_argument(
        "--gas-oil-boiler-ban-date",
        default=datetime.datetime(2035, 1, 1),
        type=convert_to_datetime,
    )

    parser.add_argument(
        "--gas-oil-boiler-ban-announce-date",
        default=datetime.datetime(2025, 1, 1),
        type=convert_to_datetime,
    )

    # SOURCE: Default values from https://energysavingtrust.org.uk/about-us/our-data/ (England, Scotland and Wales)
    # These fuel prices were last updated in November 2021, based on predicted fuel prices for 2022
    parser.add_argument("--price-gbp-per-kwh-gas", type=float, default=0.062)
    parser.add_argument("--price-gbp-per-kwh-electricity", type=float, default=0.245)
    parser.add_argument("--price-gbp-per-kwh-oil", type=float, default=0.068)

    parser.add_argument(
        "--campaign-target-heat-pump-awareness-date",
        action="append",
        type=map_string_to_datetime_float_dict,
        help="A factor by which heat pump awareness will increase by a specified date.",
        metavar="{YYYY-MM-DD:heat_pump_awareness}",
    )

    return parser.parse_args(args)


def validate_args(args):
    if args.gas_oil_boiler_ban_announce_date > args.gas_oil_boiler_ban_date:
        raise ValueError(
            f"Boiler ban announcement date must be on or before ban date, got gas_oil_boiler_ban_date:{args.gas_oil_boiler_ban_date}, gas_oil_boiler_ban_announce_date:{args.gas_oil_boiler_ban_announce_date}"
        )

    print(args.campaign_target_heat_pump_awareness_date)
    if args.campaign_target_heat_pump_awareness_date is not None:
        # Check that target awareness inputs increase over the model horizon
        campaigns = args.campaign_target_heat_pump_awareness_date[0]
        campaigns[args.heat_pump_awareness] = args.start_datetime
        campaigns = dict(sorted(campaigns.items()))
        increasing_awareness = sorted(list(campaigns.values())) == list(campaigns.values())
        if not increasing_awareness:
            raise ValueError(
                f"Campaign target awareness must be greater than or equal to the population heat pump awareness, got campaign_target_heat_pump_awareness:{args.campaign_target_heat_pump_awareness_date}, heat_pump_awareness:{args.heat_pump_awareness}"
            )


if __name__ == "__main__":

    args = parse_args()
    validate_args(args)

    logger.info(
        "parsed arguments",
        **{
            key: value
            for key, value in vars(args).items()
            if not isinstance(value, pd.DataFrame)
        },
    )

    random.seed(args.seed)

    try:
        history = create_and_run_simulation(
            args.start_datetime,
            args.step_interval,
            args.time_steps,
            args.households if args.households is not None else args.bigquery,
            args.heat_pump_awareness,
            args.annual_renovation_rate,
            args.household_num_lookahead_years,
            args.heating_system_hassle_factor,
            args.rented_heating_system_hassle_factor,
            args.intervention,
            args.all_agents_heat_pump_suitable,
            args.gas_oil_boiler_ban_date,
            args.gas_oil_boiler_ban_announce_date,
            args.price_gbp_per_kwh_gas,
            args.price_gbp_per_kwh_electricity,
            args.price_gbp_per_kwh_oil,
            args.air_source_heat_pump_price_discount_date,
            args.heat_pump_installer_count,
            args.heat_pump_installer_annual_growth_rate,
            ENGLAND_WALES_ANNUAL_NEW_BUILDS if args.include_new_builds else None,
            args.campaign_target_heat_pump_awareness_date,
        )

        with smart_open.open(args.history_file, "w") as file:
            write_jsonlines(history, file)

    except Exception:
        logger.exception("simulation failed")
        sys.exit(1)

    logger.info("simulation complete")
