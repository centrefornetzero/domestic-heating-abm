import argparse
import datetime
import os
import random
import uuid
from functools import partial

import pandas as pd
import smart_open
from dateutil.relativedelta import relativedelta

from abm import write_jsonlines
from simulation.constants import InterventionType
from simulation.model import create_and_run_simulation


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

    parser = argparse.ArgumentParser()

    households = parser.add_mutually_exclusive_group(required=True)
    households.add_argument("households", type=pd.read_parquet, nargs="?")
    households.add_argument(
        "--bigquery",
        help="Generate household agents from BigQuery result.",
        type=partial(
            pd.read_gbq, project_id=os.getenv("PROJECT_ID"), use_bq_storage_api=True
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
        default=datetime.datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        ),
    )

    parser.add_argument(
        "--step-interval",
        type=convert_to_months_relativedelta,
        default=relativedelta(months=1),
        metavar="MONTHS",
    )

    parser.add_argument("--steps", dest="time_steps", type=int, default=100)
    parser.add_argument("--heat-pump-awareness", type=float, default=0.4)
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
        "--intervention",
        action="append",
        help="Valid interventions are: "
        + ", ".join(member.name for member in InterventionType),
        type=map_string_to_intervention_type_enum,
    )

    parser.add_argument(
        "--all-agents-heat-pump-suitable",
        default=False,
        type=bool,
        help="When True, 100pc of households are assumed suitable for heat pumps. When False, households are assigned a heat pump suitability as per the source data file.",
    )

    parser.add_argument(
        "--air-source-heat-pump-discount-factor-2022",
        type=float,
        default=0.1,
        help="A factor by which current (2021) air source heat pump unit+install costs will have declined by, as of the end of 2022",
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

    # SOURCE: Default values from https://energysavingtrust.org.uk/about-us/our-data/ (England, Scotland and Wales)
    # These fuel prices were last updated in November 2021, based on predicted fuel prices for 2022
    parser.add_argument("--price-gbp-per-kwh-gas", type=float, default=0.0465)
    parser.add_argument("--price-gbp-per-kwh-electricity", type=float, default=0.2006)
    parser.add_argument("--price-gbp-per-kwh-oil", type=float, default=0.0482)

    return parser.parse_args(args)


if __name__ == "__main__":
    args = parse_args()

    random.seed(args.seed)
    history = create_and_run_simulation(
        args.start_datetime,
        args.step_interval,
        args.time_steps,
        args.households if args.households is not None else args.bigquery,
        args.heat_pump_awareness,
        args.annual_renovation_rate,
        args.household_num_lookahead_years,
        args.heating_system_hassle_factor,
        args.intervention,
        args.air_source_heat_pump_discount_factor_2022,
        args.all_agents_heat_pump_suitable,
        args.gas_oil_boiler_ban_date,
        args.price_gbp_per_kwh_gas,
        args.price_gbp_per_kwh_electricity,
        args.price_gbp_per_kwh_oil,
    )

    if args.history_file.startswith("gs://"):
        history = list(history)

    with smart_open.open(args.history_file, "w") as file:
        write_jsonlines(history, file)
