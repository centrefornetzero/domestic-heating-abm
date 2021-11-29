import argparse
import datetime

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

    parser.add_argument("--steps", dest="num_steps", type=int, default=100)
    parser.add_argument("--num-households", type=int, default=10)
    parser.add_argument("--history-filename", default="history.jsonl")
    parser.add_argument("--household-distribution", type=pd.read_csv)
    parser.add_argument("--heat-pump-awareness", type=float, default=0.4)

    return parser.parse_args(args)


args = parse_args()

history = create_and_run_simulation(
    args.start_datetime,
    args.step_interval,
    args.num_steps,
    args.num_households,
    args.household_distribution,
    args.heat_pump_awareness,
)

write_jsonlines(history, args.history_filename)
