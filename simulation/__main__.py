import argparse
import datetime
import random

import pandas as pd

from abm import write_jsonlines
from simulation.model import create_and_run_simulation


def parse_args(args=None):
    def convert_to_datetime(date_string):
        return datetime.datetime.strptime(date_string, "%Y-%m-%d")

    def convert_to_timedelta(minutes_string):
        return datetime.timedelta(minutes=int(minutes_string))

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start-date",
        dest="start_datetime",
        type=convert_to_datetime,
        default=datetime.datetime.combine(datetime.date.today(), datetime.time()),
    )

    parser.add_argument(
        "--step-interval",
        type=convert_to_timedelta,
        default=datetime.timedelta(minutes=1440),
    )

    parser.add_argument("--steps", dest="time_steps", type=int, default=100)
    parser.add_argument("--num-households", type=int, default=10)
    parser.add_argument("--history-filename", default="history.jsonl")
    parser.add_argument("--household-distribution", type=pd.read_csv)
    parser.add_argument("--heat-pump-awareness", type=float, default=0.4)
    parser.add_argument("--annual-renovation-rate", type=float, default=0.05)
    parser.add_argument(
        "--household-num-lookahead-years",
        type=int,
        default=3,
        help="The number of years households look ahead when making purchasing decisions; any cash flows to be exchanged further than this number of years in the future are valued at £0 by households",
    )

    def restrict_between_0_and_1(input_value: float):
        return max(min(input_value, 0), 1)

    parser.add_argument(
        "--heating-system-hassle-factor",
        type=restrict_between_0_and_1,
        default=0.3,
        help="A value between 0 and 1 which suppresses the likelihood of a household choosing a given heating system (the higher the value, the lower the likelihood)",
    )

    parser.add_argument("--random-seed", type=int)

    return parser.parse_args(args)


if __name__ == "__main__":

    args = parse_args()

    random.seed(args.random_seed)
    history = create_and_run_simulation(
        args.start_datetime,
        args.step_interval,
        args.time_steps,
        args.num_households,
        args.household_distribution,
        args.heat_pump_awareness,
        args.annual_renovation_rate,
        args.household_num_lookahead_years,
        args.heating_system_hassle_factor,
        args.random_seed,
    )

    write_jsonlines(history, args.history_filename)
