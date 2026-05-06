from __future__ import annotations

import pytest

from backtester.cli import build_parser, parse_int_list


def test_parse_int_list() -> None:
    assert parse_int_list("5,10, 20") == [5, 10, 20]


def test_run_parser_accepts_required_arguments() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run",
            "--ticker",
            "AAPL",
            "--start",
            "2020-01-01",
            "--end",
            "2021-01-01",
            "--strategy",
            "momentum",
        ]
    )

    assert args.command == "run"
    assert args.strategy == "momentum"


def test_invalid_strategy_exits_cleanly() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "run",
                "--ticker",
                "AAPL",
                "--start",
                "2020-01-01",
                "--end",
                "2021-01-01",
                "--strategy",
                "bad",
            ]
        )
