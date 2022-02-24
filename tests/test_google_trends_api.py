import datetime
import os

import pytest
from loguru import logger

import google_trends_api
from google_trends_api import constants

PROXIES = 'http://localhost:10001'


class TestGoogleTrendsApi:
    @pytest.fixture
    def google_trends_api_obj(self):
        return google_trends_api.GoogleTrendsApi(
            proxies=PROXIES,
        )

    def test__get_cookies(self, google_trends_api_obj):
        cookies = google_trends_api_obj._get_cookies()
        assert cookies != {}

    async def test__get_widget(self, google_trends_api_obj):
        widget = await google_trends_api_obj._get_widget(
            'nft',
            constants.WidgetId.TIME_SERIES,
            timezone=0,
            time_range=constants.TimeRange.PAST_1D)
        assert widget != {}
        assert widget['id'] == constants.WidgetId.TIME_SERIES

    async def test__get_widget_with_custom_time_range(self, google_trends_api_obj):
        start_datetime = datetime.datetime(year=2022, month=1, day=23, hour=0)
        end_datetime = datetime.datetime(year=2022, month=1, day=30, hour=23)
        widget = await google_trends_api_obj._get_widget(
            'nft',
            constants.WidgetId.TIME_SERIES,
            timezone=0,
            custom_time_range=(start_datetime, end_datetime))
        assert widget != {}
        assert widget['id'] == constants.WidgetId.TIME_SERIES

    async def test_get_hourly_data(self, google_trends_api_obj):
        start_datetime = datetime.datetime(year=2022, month=1, day=20, hour=0)
        end_datetime = datetime.datetime(year=2022, month=1, day=31, hour=3)
        async for time, value in google_trends_api_obj.get_hourly_data('nft', start_datetime, end_datetime):
            assert isinstance(time, int) and time > 1000000000
            assert isinstance(value, int) and value <= 100
