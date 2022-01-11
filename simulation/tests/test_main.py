import datetime
import os
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from abm import read_jsonlines
from simulation.__main__ import parse_args


@pytest.fixture
def mandatory_args(tmp_path):
    households_csv_file = Path(__file__).parent / "household_population.csv"
    households = pd.read_csv(households_csv_file)
    households_parquet_file = tmp_path / "household_population.parquet"
    households.to_parquet(households_parquet_file)

    return [
        str(households_parquet_file),
        str(tmp_path / "output.jsonl"),
    ]


class TestParseArgs:
    def test_mandatory_args(self, mandatory_args):
        args = parse_args(mandatory_args)
        assert isinstance(args.household_population_file, pd.DataFrame)
        assert args.history_file == mandatory_args[1]

    def test_start_date_returns_datetime(self, mandatory_args):
        args = parse_args([*mandatory_args, "--start-date", "2021-01-01"])
        assert args.start_datetime == datetime.datetime(2021, 1, 1)

    def test_start_date_default_is_today_at_midnight(self, mandatory_args):
        args = parse_args(mandatory_args)
        assert args.start_datetime == datetime.datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def test_default_seed_is_current_datetime_string(self, mandatory_args):
        datetime_before = datetime.datetime.now()
        args = parse_args(mandatory_args)
        datetime_after = datetime.datetime.now()
        assert (
            datetime_before
            < datetime.datetime.fromisoformat(args.seed)
            < datetime_after
        )

    def test_custom_seed(self, mandatory_args):
        args = parse_args([*mandatory_args, "--seed", "1970-01-01"])
        assert args.seed == "1970-01-01"

    def test_custom_seed_with_non_isoformat_datetime_fails(self, mandatory_args):
        with pytest.raises(SystemExit):
            parse_args([*mandatory_args, "--seed", "hello"])

    def test_heating_system_hassle_factor(self, mandatory_args):
        args = parse_args([*mandatory_args, "--heating-system-hassle-factor", "0.5"])
        assert args.heating_system_hassle_factor == 0.5

    def test_heating_system_hassle_factor_must_be_between_0_and_1(self, mandatory_args):
        with pytest.raises(SystemExit):
            parse_args([*mandatory_args, "--heating-system-hassle-factor", "10"])

    def test_help_flag(self):
        with pytest.raises(SystemExit):
            parse_args(["-h"])


def assert_histories_equal(first_history, second_history):
    first_agent_history, first_model_history = first_history
    second_agent_history, second_model_history = second_history
    pd.testing.assert_frame_equal(first_agent_history, second_agent_history)
    pd.testing.assert_frame_equal(first_model_history, second_model_history)


def test_running_simulation_twice_gives_non_identical_results(mandatory_args):
    args = ["python", "-m", "simulation", *mandatory_args]
    history_file = mandatory_args[1]

    subprocess.run(args, check=True)
    first_history = read_jsonlines(history_file)

    subprocess.run(args, check=True)
    second_history = read_jsonlines(history_file)

    with pytest.raises(AssertionError):
        assert_histories_equal(first_history, second_history)


def test_running_simulation_twice_with_same_seed_gives_identical_results(
    mandatory_args,
):
    args = ["python", "-m", "simulation", *mandatory_args, "--seed", "2021-01-01"]
    history_file = mandatory_args[1]

    subprocess.run(args, check=True)
    first_history = read_jsonlines(history_file)

    subprocess.run(args, check=True)
    second_history = read_jsonlines(history_file)

    assert_histories_equal(first_history, second_history)


def test_python_hash_randomization_is_disabled():
    assert os.environ["PYTHONHASHSEED"] == "0"
