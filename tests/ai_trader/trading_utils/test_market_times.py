from datetime import datetime

import pytest

from ai_trader.trading_utils.market_times import is_epic_open, only_open_epics


@pytest.mark.parametrize(
    "date_time, epic, expected",
    [
        # US
        ("2026-10-12 17:00:00+00:00", "IX.D.SPTRD.DAILY.IP", True), # Monday
        ("2026-10-14 02:00:00+00:00", "IX.D.SPTRD.DAILY.IP", False), # Wednesday
        ("2026-10-14 13:29:00+00:00", "IX.D.SPTRD.DAILY.IP", False), # Wednesday
        ("2026-10-14 13:31:00+00:00", "IX.D.SPTRD.DAILY.IP", True), # Wednesday
        ("2026-10-14 17:00:00+00:00", "IX.D.SPTRD.DAILY.IP", True), # Wednesday
        ("2026-10-14 20:29:00+00:00", "IX.D.SPTRD.DAILY.IP", True), # Wednesday
        ("2026-10-14 20:31:00+00:00", "IX.D.SPTRD.DAILY.IP", False), # Wednesday
        ("2026-10-16 17:00:00+00:00", "IX.D.SPTRD.DAILY.IP", True), # Friday
        ("2026-10-17 17:00:00+00:00", "IX.D.SPTRD.DAILY.IP", False), # Saturday
        ("2026-10-18 17:00:00+00:00", "IX.D.SPTRD.DAILY.IP", False), # Sunday
        #UK
        ("2026-10-12 12:00:00+00:00", "IX.D.FTSE.DAILY.IP", True), # Monday
        ("2026-10-14 02:00:00+00:00", "IX.D.FTSE.DAILY.IP", False), # Wednesday
        ("2026-10-14 06:59:00+00:00", "IX.D.FTSE.DAILY.IP", False), # Wednesday
        ("2026-10-14 07:01:00+00:00", "IX.D.FTSE.DAILY.IP", True), # Wednesday
        ("2026-10-14 12:00:00+00:00", "IX.D.FTSE.DAILY.IP", True), # Wednesday
        ("2026-10-14 15:29:00+00:00", "IX.D.FTSE.DAILY.IP", True), # Wednesday
        ("2026-10-14 15:31:00+00:00", "IX.D.FTSE.DAILY.IP", False), # Wednesday
        ("2026-10-16 12:00:00+00:00", "IX.D.FTSE.DAILY.IP", True), # Friday
        ("2026-10-17 12:00:00+00:00", "IX.D.FTSE.DAILY.IP", False), # Saturday
        ("2026-10-18 12:00:00+00:00", "IX.D.FTSE.DAILY.IP", False), # Sunday
    ]
)
def test_is_epic_open_us(date_time: str, epic: str, expected: bool):
    assert is_epic_open(epic, datetime.fromisoformat(date_time)) == expected


def test_only_open_epics():
    # given
    date_time = "2026-10-14 07:01:00+00:00"
    epics = ["IX.D.SPTRD.DAILY.IP", "IX.D.FTSE.DAILY.IP"]

    # when
    open_epics = only_open_epics(epics, datetime.fromisoformat(date_time))

    # then
    assert open_epics == ["IX.D.FTSE.DAILY.IP"]