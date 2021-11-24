from abm import write_jsonlines
from simulation.model import create_and_run_simulation
from simulation.settings import *

history = create_and_run_simulation(
    START_DATETIME,
    STEP_INTERVAL,
    NUM_STEPS,
    NUM_HOUSEHOLDS,
    HOUSEHOLD_DISTRIBUTION,
)

write_jsonlines(history, HISTORY_FILENAME)
