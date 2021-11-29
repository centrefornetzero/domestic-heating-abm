import argparse
import datetime

import pandas as pd


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--household-distribution", type=pd.read_csv)
    return parser.parse_args(args)


# simulation run parameters
START_DATETIME = datetime.datetime.combine(datetime.date.today(), datetime.time())
STEP_INTERVAL = datetime.timedelta(minutes=1440)
NUM_STEPS = 365
NUM_HOUSEHOLDS = 500
HISTORY_FILENAME = "history.jsonl"

# agent parameters
HEAT_PUMP_AWARENESS = 0.4
