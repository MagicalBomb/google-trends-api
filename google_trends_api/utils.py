import datetime


def datetime_range(
        start: datetime.datetime,
        end: datetime.datetime,
        step: datetime.timedelta,
        can_overflow: bool = False,
):
    """
    Generator that yields datetime objects [start, end) in steps of step.
    If can_overflow is True, the generator will yield the end value
    """
    current = start
    while current < end:
        yield current
        current += step
    if can_overflow:
        yield current


def parse_timezone_in_google_way(dt: datetime.datetime) -> int:
    """
    Returns the timezone offset in minutes from UTC.

    If dt.tzinfo is None, use local timezone.
    """
    utc_tz = datetime.timezone.utc
    if dt.tzinfo is None:
        dt = dt.astimezone()

    tz_info = dt.tzinfo
    return -int(tz_info.utcoffset(None).total_seconds() / 60)


async def alist(async_gen):
    lst = []
    async for item in async_gen:
        lst.append(item)
    return lst


def find_index(lst, key):
    for i, item in enumerate(lst):
        if key(item):
            return i
