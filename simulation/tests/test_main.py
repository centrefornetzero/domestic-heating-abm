import datetime

import pytest

from simulation.__main__ import parse_args


class TestParseArgs:
    def test_start_date_returns_datetime(self):
        args = parse_args(["--start-date", "2021-01-01"])
        assert args.start_datetime == datetime.datetime(2021, 1, 1)

    def test_start_date_default_is_now(self):
        args = parse_args([])
        assert args.start_datetime.date() == datetime.date.today()
        assert args.start_datetime < datetime.datetime.now()

    def test_default_seed_is_current_datetime_string(self):
        datetime_before = datetime.datetime.now()
        args = parse_args([])
        datetime_after = datetime.datetime.now()
        assert (
            datetime_before
            < datetime.datetime.fromisoformat(args.seed)
            < datetime_after
        )

    def test_custom_seed(self):
        args = parse_args(["--seed", "1970-01-01"])
        assert args.seed == "1970-01-01"

    def test_custom_seed_with_non_isoformat_datetime_fails(self):
        with pytest.raises(SystemExit):
            parse_args(["--seed", "hello"])
