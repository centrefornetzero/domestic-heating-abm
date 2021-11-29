from abm import write_jsonlines
from simulation.model import create_and_run_simulation
from simulation.settings import (
    HISTORY_FILENAME,
    NUM_HOUSEHOLDS,
    NUM_STEPS,
    START_DATETIME,
    STEP_INTERVAL,
    parse_args,
)

args = parse_args()

history = create_and_run_simulation(
    START_DATETIME,
    STEP_INTERVAL,
    NUM_STEPS,
    NUM_HOUSEHOLDS,
    args.household_distribution,
)

write_jsonlines(history, HISTORY_FILENAME)
