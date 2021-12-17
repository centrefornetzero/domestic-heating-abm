import datetime
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from simulation.__main__ import parse_args


@pytest.fixture
def mandatory_args(tmp_path):
    return [
        str(Path(__file__).parent / "household_attributes.csv"),
        str(tmp_path / "output.jsonl"),
    ]


class TestParseArgs:
    def test_mandatory_args(self, mandatory_args):
        args = parse_args(mandatory_args)
        assert isinstance(args.household_distribution_file, pd.DataFrame)
        assert args.history_file == mandatory_args[1]

    def test_start_date_returns_datetime(self, mandatory_args):
        args = parse_args([*mandatory_args, "--start-date", "2021-01-01"])
        assert args.start_datetime == datetime.datetime(2021, 1, 1)

    def test_start_date_default_is_now(self, mandatory_args):
        args = parse_args(mandatory_args)
        assert args.start_datetime.date() == datetime.date.today()
        assert args.start_datetime < datetime.datetime.now()


def test_running_simulation_twice_gives_non_identical_results(mandatory_args):
    args = ["python", "-m", "simulation", *mandatory_args]
    history_file = mandatory_args[1]

    subprocess.run(args, check=True)
    with open(history_file, "r") as f:
        first_history = f.readlines()

    subprocess.run(args, check=True)
    with open(history_file, "r") as f:
        second_history = f.readlines()

    assert first_history != second_history
