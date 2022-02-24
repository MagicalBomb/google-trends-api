import datetime
import json
from typing import List, Union, Tuple

import httpx

from google_trends_api import constants, utils
from google_trends_api.utils import datetime_range


class GoogleTrendsApi:
    def __init__(self, *, host_language='en-US', proxies=None):
        """
        timezone: timezone offset in minutes.
        """
        self.host_language = host_language
        self.proxies = proxies
        self.http_client = httpx.AsyncClient(
            cookies=self._get_cookies(),
            proxies=proxies)

    def _get_cookies(self) -> dict:
        resp = httpx.get(
            url='https://trends.google.com/',
            params={'geo': 'US'},  # Seems keep the US is always the best choice.
            follow_redirects=True,
            proxies=self.proxies)
        return {k: v for k, v in resp.cookies.items() if k == 'NID'}

    async def _get_widget(
            self,
            keyword,
            widget_id: constants.WidgetId,
            timezone: int,
            time_range: constants.TimeRange = None,
            custom_time_range: Tuple[datetime.datetime, datetime.datetime] = None,
            *,
            frequency: constants.Frequency = constants.Frequency.HOURLY,
            geo: str = "",  # Country abbreviation. empty string means worldwide
    ) -> dict:
        """
        :param timezone: timezone offset in minutes.

        Notice that the difference bewteen start_datetime and end_datetime must be less than 8 days, if frequency is HOURLY.
        """
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
            'hl': self.host_language,
            'tz': timezone,
            'req': param_req,
        }

        resp = await self.http_client.get(constants.API.EXPLORE, params=query)
        js = json.loads(resp.text[5:])
        for widget in js['widgets']:
            if widget['id'] == widget_id:
                return widget

    async def get_hourly_data(
            self,
            keyword: str,
            start_datetime: datetime.datetime,
            end_datetime: datetime.datetime,
            *,
            geo: str = "",  # Country abbreviation. empty string means worldwide
    ) -> Tuple[int, int]:
        """
        :param keyword:
        :param start_datetime
        :param end_datetime
        :return: yield (timestamp, hourly_trends)

        datetime.tzinfo is used to specify the timezone.
        If both start_datetime and end_datetime all specify timezone, the timezone of start_datetime will be used.
        If both start_datetime and end_datetime do not specify timezone, the timezone of the current system will be used.
        """
        timedelta = end_datetime - start_datetime
        if timedelta.total_seconds() < 3600:
            raise ValueError('start_datetime must be earlier than end_datetime at least 1 hour')

        # Get timezone in minutes
        timezone: int = utils.parse_timezone(start_datetime if start_datetime.tzinfo else end_datetime)

        # Get hourly data
        step = datetime.timedelta(days=7)
        for left in datetime_range(start_datetime, end_datetime, step):
            right = min(left + step, end_datetime)
            widget = await self._get_widget(keyword, constants.WidgetId.TIME_SERIES, timezone=timezone, geo=geo, custom_time_range=(left, right))
            query = {
                'hl': self.host_language,
                'tz': timezone,
                'token': widget['token'],
                'req': widget['request'],
            }
            resp = await self.http_client.get(constants.API.TRENDS_OVER_TIME, params=query)
            js = json.loads(resp.text[5:])

            # Yield hourly data
            for item in js['default']['timelineData']:
                yield int(item['time']), item['value'][0]
