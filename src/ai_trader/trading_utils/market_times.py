from datetime import time, datetime, timezone
from zoneinfo import ZoneInfo

MARKET_TIMES = {
    "US": {
        "timeZone": ZoneInfo("America/New_York"),
        "open": time(9, 30),
        "close": time(16, 30)
    },
    "UK": {
        "timeZone": ZoneInfo("Europe/London"),
        "open": time(8, 0),
        "close": time(16, 30)
    },
    "DE": {
        "timeZone": ZoneInfo("Europe/Berlin"),
        "open": time(9, 0),
        "close": time(17, 30)
    },
}

EPIC_MARKET = {
    # US
    "IX.D.DOW.DAILY.IP": "US",
    "IX.D.NASDAQ.CASH.IP": "US",
    "UD.D.SOXXUS.DAILY.IP": "US",
    "IX.D.SPTRD.DAILY.IP": "US",
    # UK
    "IX.D.FTSE.DAILY.IP": "UK",
    # DE
    "IX.D.DAX.DAILY.IP": "DE",
}

def is_epic_open(epic_id: str, utc_datetime: datetime) -> bool:
    market_code = EPIC_MARKET.get(epic_id, 'US')

    market_info = MARKET_TIMES[market_code]
    tz = market_info["timeZone"]
    open_time = market_info["open"]
    close_time = market_info["close"]

    local_dt = utc_datetime.astimezone(tz)

    if local_dt.weekday() >= 5:
        return False

    current_time = local_dt.time()
    return open_time <= current_time <= close_time

def only_open_epics(epics: list[str], utc_datetime: datetime) -> list[str]:
    return [epic for epic in epics if is_epic_open(epic, utc_datetime)]