from datetime import datetime, timezone, timedelta

from google_trends_api import constants, utils, _api
from google_trends_api.utils import datetime_range, alist


async def _hourly_data(
        keyword: str,
        start_datetime: datetime,
        end_datetime: datetime,
        tzinfo: timezone = None,
        *,
        geo: str = "",
        host_language: str = "en-US",
):
    """
    Get hourly google trends data for a keyword in every 7 day period.
    Note hourly trends value is relative to their period, not a absolute value.

    :param keyword: The keyword to get data for.
    :param start_datetime: The start datetime to get data for.
    :param end_datetime: The end datetime to get data for.
    :param tzinfo: The timezone to get data for. Defaults to local timezone.

    @return: yield (timestamp, value)
    """

    # Currently, the only way to get hourly data is requesting api with time range of 7 day every time
    cookies = await _api.get_cookies()

    if not tzinfo:
        # Set tzinfo to local timezone
        tzinfo = start_datetime.astimezone().tzinfo
        timezone_offset = utils.parse_timezone_in_google_way(start_datetime)
    else:
        timezone_offset = -int(tzinfo.utcoffset(None).total_seconds() / 60)

    start_datetime = start_datetime + timedelta(minutes=timezone_offset)
    start_datetime = start_datetime.replace(tzinfo=tzinfo)
    end_datetime = end_datetime + timedelta(minutes=timezone_offset)
    end_datetime = end_datetime.replace(tzinfo=tzinfo)

    step = timedelta(days=7)
    for dt in utils.datetime_range(start_datetime, end_datetime, step, can_overflow=True):
        widgets = await _api.get_widgets(
            keyword,
            timezone_offset=timezone_offset,
            cookies=cookies,
            custom_time_range=(dt, dt + step),
            frequency=constants.Frequency.HOURLY,
            geo=geo,
            host_language=host_language,
        )

        js = await _api.interest_over_time(
            cookies=cookies,
            widgets=widgets,
            timezone_offset=timezone_offset,
            host_language=host_language,
        )
        hourly_items = js['default']['timelineData']

        for item in hourly_items:
            timestamp = int(item['time'])
            if item['hasData'][0] and datetime.fromtimestamp(timestamp, tz=tzinfo) < (end_datetime - timedelta(minutes=timezone_offset)):
                yield timestamp, item['value'][0]


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
