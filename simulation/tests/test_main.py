import datetime

from simulation.__main__ import parse_args


class TestParseArgs:
    def test_start_date_returns_datetime(self):
        args = parse_args(["--start-date", "2021-01-01"])
        assert args.start_datetime == datetime.datetime(2021, 1, 1)

    def test_start_date_default_is_now(self):
        args = parse_args([])
        assert args.start_datetime.date() == datetime.date.today()
        assert args.start_datetime < datetime.datetime.now()
