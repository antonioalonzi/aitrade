from datetime import datetime
from zoneinfo import ZoneInfo


def to_localised_time(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    dt_local_naive = dt.astimezone(ZoneInfo('Europe/London')).replace(tzinfo=None)
    return dt_local_naive.replace(tzinfo=ZoneInfo('UTC'))

def to_localised_time_panda(time):
    return time.dt.tz_convert('Europe/London').dt.tz_localize(None)