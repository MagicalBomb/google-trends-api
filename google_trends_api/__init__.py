from datetime import datetime, timezone, timedelta
from functools import partial
from typing import List

from google_trends_api import constants, utils, _api
from google_trends_api.utils import datetime_range, alist


async def _seven_days_hourly_data(
        keyword: str,
        start_dt: datetime,
        tz: timezone,
        *,
        cookies: dict = None,
        geo: str = "",
        host_language: str = "en-US",
):
    """
    Get 7 days google trends data for a keyword. [start_datetime, start_datetime + 7 days)
    This seems the only way to fetch hourly data by using google trends official pi

    :param keyword: The keyword to get data for.
    :param start_datetime: The start datetime to get data for.
    :param tzinfo: The timezone to get data for. Defaults to local timezone.

    @return: yield (timestamp, value)
    """
    cookies = cookies or await _api.get_cookies()
    tz_offset = -int(tz.utcoffset(None).total_seconds() / 60)
    end_dt = (start_dt + timedelta(days=7))

    start_dt = start_dt + timedelta(minutes=tz_offset)
    end_dt = end_dt + timedelta(minutes=tz_offset)
    start_dt = start_dt.replace(tzinfo=tz)
    end_dt = end_dt.replace(tzinfo=tz)

    widgets = await _api.get_widgets(
        keyword,
        timezone_offset=tz_offset,
        cookies=cookies,
        custom_time_range=(start_dt, end_dt),
        frequency=constants.Frequency.HOURLY,
        geo=geo,
        host_language=host_language,
    )

    js = await _api.interest_over_time(
        cookies=cookies,
        widgets=widgets,
        timezone_offset=tz_offset,
        host_language=host_language,
    )
    hourly_items = js['default']['timelineData']

    for item in hourly_items:
        timestamp = int(item['time'])
        if item['hasData'][0] and datetime.fromtimestamp(timestamp, tz=tz) < (end_dt - timedelta(minutes=tz_offset)):
            yield timestamp, item['value'][0]


async def _hourly_data(
        keyword: str,
        start_dt: datetime,
        end_dt: datetime,
        tz: timezone,
        *,
        cookies: dict = None,
        geo: str = "",
        host_language: str = "en-US",
) -> List[list]:
    """
    Get hourly google trends data for a keyword in every 7 day period. [start_datetime, end_datetime)
    Note hourly trends value is relative to their period, not a absolute value.

    :param keyword: The keyword to get data for.
    :param start_datetime: The start datetime to get data for.
    :param end_datetime: The end datetime to get data for.
    :param tzinfo: The timezone to get data for. Defaults to local timezone.

    @return: yield (timestamp, value)
    """

    # Currently, the only way to get hourly data is requesting api with time range of 7 day every time
    cookies = cookies or await _api.get_cookies()

    start_dt = start_dt.replace(tzinfo=tz)
    end_dt = end_dt.replace(tzinfo=tz)
    end_ts = int(end_dt.timestamp())

    step = timedelta(days=7)
    for dt in utils.datetime_range(start_dt, end_dt, step, can_overflow=True):
        _7days_items = await alist(_seven_days_hourly_data(
            keyword,
            dt,
            tz,
            cookies=cookies,
            geo=geo,
            host_language=host_language,
        ))
        if _7days_items[-1][0] < end_ts:
            yield _7days_items
        else:
            index = utils.find_index(_7days_items, lambda item: item[0] >= end_ts)
            if index != 0:  # Avoid yield [], it's meaningless and looks foolish
                yield _7days_items[:index]


async def seven_days_data(
    keyword: str,
    start_datetime: datetime,
    tzinfo: timezone = None,
    *,
    geo: str = "",
    host_language: str = "en-US",
):
    """
    Get 7 day google trends data for a keyword

    :param keyword: The keyword to get data for.
    :param start_datetime: The start datetime to get data for.
    :param tzinfo: The timezone to get data for. Defaults to local timezone.

    @return: yield (timestamp, value)
    """

    async for time, value in _hourly_data(keyword, start_datetime, start_datetime + timedelta(days=7), tzinfo=tzinfo, geo=geo, host_language=host_language):
        yield time, value


async def hourly_data(
        keyword: str,
        start_datetime: datetime,
        end_datetime: datetime,
        tzinfo: timezone = None,
        *,
        geo: str = "",
        host_language: str = "en-US",
):
    """
    Get hourly google trends data for a keyword.
    Note hourly trends value is relative to the first 7 days of the start_datetime
    """
    timedelta_7days = timedelta(days=7)
    timedelta_1hour = timedelta(hours=1)

    first_7days = await alist(seven_days_data(keyword, start_datetime, tzinfo, geo=geo, host_language=host_language))
    second_7days = await alist(seven_days_data(keyword, start_datetime + timedelta_7days, tzinfo, geo=geo, host_language=host_language))
