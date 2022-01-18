import datetime
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

import simulation.__main__
from abm import read_jsonlines
from simulation.__main__ import parse_args
from simulation.constants import InterventionType


@pytest.fixture
def output_file(tmp_path):
    return str(tmp_path / "output.jsonl")


@pytest.fixture
def households_file(tmp_path):
    households_csv_file = Path(__file__).parent / "household_population.csv"
    households = pd.read_csv(households_csv_file)
    households_parquet_file = tmp_path / "household_population.parquet"
    households.to_parquet(households_parquet_file)
    return str(households_parquet_file)


@pytest.fixture
def mandatory_local_args(households_file, output_file):
    return [households_file, output_file]


@pytest.fixture
def mock_read_gbp(monkeypatch):
    mock = Mock()
    mock.return_value = pd.DataFrame({"bq": ["mocked_return_value"]})
    monkeypatch.setattr(simulation.__main__.pd, "read_gbq", mock)
    return mock


class TestParseArgs:
    def test_mandatory_local_args(self, mandatory_local_args):
        args = parse_args(mandatory_local_args)
        assert isinstance(args.households, pd.DataFrame)
        assert args.history_file == mandatory_local_args[1]

    def test_start_date_returns_datetime(self, mandatory_local_args):
        args = parse_args([*mandatory_local_args, "--start-date", "2021-01-01"])
        assert args.start_datetime == datetime.datetime(2021, 1, 1)

    def test_start_date_default_is_today_at_midnight(self, mandatory_local_args):
        args = parse_args(mandatory_local_args)
        assert args.start_datetime == datetime.datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def test_default_seed_is_current_datetime_string(self, mandatory_local_args):
        datetime_before = datetime.datetime.now()
        args = parse_args(mandatory_local_args)
        datetime_after = datetime.datetime.now()
        assert (
            datetime_before
            < datetime.datetime.fromisoformat(args.seed)
            < datetime_after
        )

    def test_custom_seed(self, mandatory_local_args):
        args = parse_args([*mandatory_local_args, "--seed", "1970-01-01"])
        assert args.seed == "1970-01-01"

    def test_custom_seed_with_non_isoformat_datetime_fails(self, mandatory_local_args):
        with pytest.raises(SystemExit):
            parse_args([*mandatory_local_args, "--seed", "hello"])

    def test_heating_system_hassle_factor(self, mandatory_local_args):
        args = parse_args(
            [*mandatory_local_args, "--heating-system-hassle-factor", "0.5"]
        )
        assert args.heating_system_hassle_factor == 0.5

    def test_heating_system_hassle_factor_must_be_between_0_and_1(
        self, mandatory_local_args
    ):
        with pytest.raises(SystemExit):
            parse_args([*mandatory_local_args, "--heating-system-hassle-factor", "10"])

    def test_help_flag(self):
        with pytest.raises(SystemExit):
            parse_args(["-h"])

    def test_bigquery_argument(self, output_file, mock_read_gbp):
        query = "select * from table"
        args = parse_args([output_file, "--bigquery", query])

        assert args.history_file == output_file

        mock_read_gbp.assert_called_with(query, project_id=None)
        pd.testing.assert_frame_equal(args.bigquery, mock_read_gbp.return_value)
        assert args.households is None

    def test_bigquery_argument_and_households_file_are_mutually_exclusive(
        self, households_file, output_file, mock_read_gbp
    ):
        with pytest.raises(SystemExit):
            parse_args(
                [
                    households_file,
                    output_file,
                    "--bigquery",
                    "select * from table",
                ]
            )

    def test_no_household_input_fails(self, output_file):
        with pytest.raises(SystemExit):
            parse_args([output_file])

    def test_intervention_argument(self, mandatory_local_args):
        args = parse_args(
            [
                *mandatory_local_args,
                "--intervention",
                "rhi",
                "--intervention",
                "boiler_upgrade_scheme",
            ]
        )

        assert args.intervention == [
            InterventionType.RHI,
            InterventionType.BOILER_UPGRADE_SCHEME,
        ]

    def test_gas_oil_boiler_ban_date_returns_datetime(self, mandatory_local_args):
        args = parse_args(
            [*mandatory_local_args, "--gas-oil-boiler-ban-date", "2030-01-01"]
        )
        assert args.gas_oil_boiler_ban_date == datetime.datetime(2030, 1, 1)

    def test_uuid_in_output_path_replaced_with_uuid_(
        self, households_file, monkeypatch
    ):
        random_uuid = "RANDOM_ID"

        def mock_uuid4():
            return random_uuid

        monkeypatch.setattr(simulation.__main__.uuid, "uuid4", mock_uuid4)

        args = parse_args([households_file, "path/to/{uuid}/history.jsonl"])
        assert args.history_file == f"path/to/{random_uuid}/history.jsonl"

    def test_fuel_price_arguments(self, mandatory_local_args):
        args = parse_args(
            [
                *mandatory_local_args,
                "--price-gbp-per-kwh-gas",
                "0.03",
                "--price-gbp-per-kwh-electricity",
                "0.33",
                "--price-gbp-per-kwh-oil",
                "0.033",
            ]
        )
        assert args.price_gbp_per_kwh_gas == 0.03
        assert args.price_gbp_per_kwh_electricity == 0.33
        assert args.price_gbp_per_kwh_oil == 0.033


def assert_histories_equal(first_history, second_history):
    first_agent_history, first_model_history = first_history
    second_agent_history, second_model_history = second_history
    pd.testing.assert_frame_equal(first_agent_history, second_agent_history)
    pd.testing.assert_frame_equal(first_model_history, second_model_history)


def test_running_simulation_twice_gives_non_identical_results(
    mandatory_local_args,
):
    args = ["python", "-m", "simulation", *mandatory_local_args]
    history_file = mandatory_local_args[1]

    subprocess.run(args, check=True)
    with open(history_file, "r") as file:
        first_history = read_jsonlines(file)

    subprocess.run(args, check=True)
    with open(history_file, "r") as file:
        second_history = read_jsonlines(file)

    with pytest.raises(AssertionError):
        assert_histories_equal(first_history, second_history)


def test_running_simulation_twice_with_same_seed_gives_identical_results(
    mandatory_local_args,
):
    args = [
        "python",
        "-m",
        "simulation",
        *mandatory_local_args,
        "--seed",
        "2021-01-01",
    ]
    history_file = mandatory_local_args[1]

    subprocess.run(args, check=True)
    with open(history_file, "r") as file:
        first_history = read_jsonlines(file)

    subprocess.run(args, check=True)
    with open(history_file, "r") as file:
        second_history = read_jsonlines(file)

    assert_histories_equal(first_history, second_history)


def test_python_hash_randomization_is_disabled():
    assert os.environ["PYTHONHASHSEED"] == "0"
