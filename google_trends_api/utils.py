import datetime


def datetime_range(
        start: datetime.datetime,
        end: datetime.datetime,
        step: datetime.timedelta
):
    """
    Generator that yields datetime objects from start to end.
    """
    while start < end:
        yield start
        start += step

    yield end


def parse_timezone_in_google_way(dt: datetime.datetime) -> int:
    """
    Returns the timezone offset in minutes from UTC.
    """
    utc_tz = datetime.timezone.utc
    if dt.tzinfo is None:
        dt = dt.astimezone()

    tz_info = dt.tzinfo
    return -int(tz_info.utcoffset(None).total_seconds() / 60)
