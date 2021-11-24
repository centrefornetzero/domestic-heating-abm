import datetime

import pandas as pd

# simulation run parameters
START_DATETIME = datetime.datetime.combine(datetime.date.today(), datetime.time())
STEP_INTERVAL = datetime.timedelta(minutes=1440)
NUM_STEPS = 365
NUM_HOUSEHOLDS = 500
HOUSEHOLD_DISTRIBUTION = pd.read_csv("simulation/data/household_attributes.csv")
HISTORY_FILENAME = "history.jsonl"

# agent parameters
HEAT_PUMP_AWARENESS = 0.4
