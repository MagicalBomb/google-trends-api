"""
Simple wrapper of google trends web api
"""
import json
from datetime import datetime, timedelta
from typing import Tuple, List

import httpx
from google_trends_api import constants


class RateLimit(Exception):
    pass


async def get_cookies(geo='US'):
    """
    Get cookies for Google Trends API.

    :param geo: Ther is no need to modify this param.
    """
    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=30) as client:
        resp = await client.get(
            url='https://trends.google.com/',
            params={'geo': geo})
        return {k: v for k, v in resp.cookies.items() if k == 'NID'}


async def get_widgets(
        keyword: str,
        timezone_offset: int,
        cookies: dict,
        time_range: constants.TimeRange = None,
        custom_time_range: Tuple[datetime, datetime] = None,
        *,
        frequency: constants.Frequency = constants.Frequency.HOURLY,
        geo: str = "",
        host_language: str = "en-US",
) -> List[dict]:
    """
    :param keyword: Keyword to search for.
    :param timezone_offset: timezone offset in minutes.
    :param time_range: Time range to search for. if both time_range nad custom_time_range are specified, use time_range.
    :param cookies: cookies returned by _api.get_cookies.
    :param custom_time_range: Custom time range to search for. Range must be less than 8 days.
    :param frequency: Frequency of data. Only avaible for custom_time_range.
    :param geo: Country abbreviation. empty string means worldwide. This param determines search region.
    :param host_language: Language of the host page. This param is useless. Normally, there is no nesscessarity to modify it

    Notice that if you are in the China (UTC+8), the timezone_offset should be -480 (note NOT 480, Google uses timezone this way...)
    """
    async with httpx.AsyncClient(cookies=cookies, verify=False, timeout=30) as client:
        if time_range is None and custom_time_range is None:
            raise ValueError('time_range or custom_time_range must be specified')

        if time_range:
            param_req = {
                'comparisonItem': [{"keyword": keyword, "geo": geo, "time": time_range}],
                "category": 0,
                "property": "",
            }
        else:
            if frequency == constants.Frequency.DAILY:
                start_datetime_str, end_datetime_str = (
                    custom_time_range[0].strftime('%Y-%m-%d'),
                    custom_time_range[1].strftime('%Y-%m-%d')
                )
            elif frequency == constants.Frequency.HOURLY:
                start_datetime_str, end_datetime_str = (
                    custom_time_range[0].strftime('%Y-%m-%dT%H'),
                    custom_time_range[1].strftime('%Y-%m-%dT%H')
                )
            param_req = {
                "comparisonItem": [
                    {"keyword": keyword, "geo": geo, "time": "{} {}".format(start_datetime_str, end_datetime_str)}
                ],
                "category": 0,
                "property": ""}

        query = {
            'hl': host_language,
            'tz': timezone_offset,
            'req': param_req,
        }

        resp = await client.get(constants.API.EXPLORE, params=query)
        if resp.status_code == 200:
            js = json.loads(resp.text[5:])
            return js['widgets']
        elif resp.status_code == 429:
            raise RateLimit(resp.text)


async def interest_over_time(
    cookies: dict,
    widgets: dict,
    timezone_offset: int,
    *,
    host_language: str = "en-US",
) -> dict:
    """
    :param widgets: widgets returned by _api.get_widgets
    :param timezone_offset: timezone offset in minutes
    :param cookies: Cookies for Google Trends API
    :param host_language: Language of the host page. This param is useless. Normally, there is no nesscessarity to modify it

    Notice that if you are in the China (UTC+8), the timezone_offset should be -480 (note NOT 480, Google uses timezone this way...)
    """
    async with httpx.AsyncClient(cookies=cookies, verify=False, timeout=30) as client:
        time_series_widget = [w for w in widgets if w['id'] == constants.WidgetId.TIME_SERIES][0]

        query = {
            'hl': host_language,
            'tz': timezone_offset,
            'token': time_series_widget['token'],
            'req': time_series_widget['request'],
        }
        resp = await client.get(constants.API.TRENDS_OVER_TIME, params=query)
        js = json.loads(resp.text[5:])
        return js
