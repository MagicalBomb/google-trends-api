import os
from datetime import datetime, timezone, timedelta
from typing import List

import loguru
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, stop_never, wait_incrementing, \
    stop_after_delay

from google_trends_api import constants, utils, _api
from google_trends_api._api import RateLimit
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


async def hourly_data(
        keyword: str,
        start_dt: datetime,
        end_dt: datetime,
        tz: timezone = None,
        *,
        cookies: dict = None,
        geo: str = "",
        host_language: str = "en-US",
        retries: int = -1,
        timeout: int = 600,
        proxy: str = None,
):
    """
    Get hourly google trends data for a keyword.
    All trends value are based on the first 7 days from start_datetime.

    :param retries: The number of retries to get data. -1 means infinite retries.
    """
    start_dt = start_dt.replace(tzinfo=tz)
    end_dt = end_dt.replace(tzinfo=tz)
    cookies = cookies or await _api.get_cookies()
    if proxy:
        os.environ['ALL_PROXY'] = proxy

    _SEVEN_DAYS = timedelta(days=7)
    _ONE_HOUR = timedelta(hours=1)

    from tenacity import _utils

    def after_log(retry_state):
        sec_format: str = "%0.3f"
        wait_fixed_seconds = retry_state.retry_object.wait.wait_fixed

        logger.warning(
            f"Google Trends Rate limit has been hit. Retrying in {wait_fixed_seconds} seconds. "
            f"fn={_utils.get_callback_name(retry_state.fn)} "
            f"attempt_count={retry_state.attempt_number} "
            f"seconds_since_start={sec_format % retry_state.seconds_since_start}s"
        )

    @retry(
        retry=retry_if_exception_type(RateLimit),
        stop=(stop_after_attempt(retries) if retries >= 0 else stop_never) | stop_after_delay(timeout),
        wait=wait_fixed(10),
        after=after_log,
        reraise=True,
    )
    async def _get_7days_hourly_data(_start_dt):
        return await alist(_seven_days_hourly_data(
            keyword=keyword,
            start_dt=_start_dt,
            tz=tz,
            cookies=cookies,
            geo=geo,
            host_language=host_language,
        ))

    def _get_last_dt(_result_item_lst) -> datetime:
        return datetime.fromtimestamp(_result_item_lst[-1][0], tz=tz)

    # ==================== Above is util ====================
    current_dt = start_dt
    result_item_lst = []

    # First
    current_group = await _get_7days_hourly_data(_start_dt=current_dt)
    ratio = 1
    result_item_lst.extend(
        [(t, v * ratio) for t, v in current_group]
    )

    while True:
        current_dt = _get_last_dt(result_item_lst)
        if current_dt >= end_dt:
            break

        current_group = await _get_7days_hourly_data(_start_dt=current_dt)
        overlaped_item = result_item_lst[-1]
        if overlaped_item[0] != current_group[0][0]:
            raise ValueError(f"Expected timestamp {overlaped_item[0]} to be equal to {current_group[0][0]}")

        ratio = overlaped_item[1] / current_group[0][1]
        result_item_lst.extend(
            [(t, v * ratio) for t, v in current_group]
        )

    end_dt = end_dt.replace(tzinfo=tz)
    index = utils.find_index(result_item_lst, lambda item: item[0] >= int(end_dt.timestamp()))
    result_item_lst = result_item_lst[:index]

    # Normalize to [0, 100]
    max_value = max(v for _, v in result_item_lst)
    return [(t, v / max_value * 100) for t, v in result_item_lst]
