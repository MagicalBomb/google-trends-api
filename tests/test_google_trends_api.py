from datetime import datetime, timezone, timedelta

import pytest

from google_trends_api import _hourly_data, seven_days_data, hourly_data, _seven_days_hourly_data
from google_trends_api.utils import alist


@pytest.mark.asyncio
async def test__seven_days_hourly_data():
    lst = await alist(_seven_days_hourly_data(
        keyword='nft',
        start_dt=datetime(2020, 1, 1, 1),
        tz=timezone(timedelta(hours=8)),
    ))

    assert lst[0][0] == int(datetime(2020, 1, 1, 1).timestamp())
    assert lst[-1][0] == int(datetime(2020, 1, 8, 0).timestamp())


@pytest.mark.asyncio
async def test__hourly_data():
    # Difference less than 7 days
    start_datetime = datetime(2022, 1, 10, 10)
    end_datetime = datetime(2022, 1, 13, 14)
    tzinfo = timezone(timedelta(hours=6))
    item_list = []
    async for timestamp, value in _hourly_data(
        keyword='nft',
        start_dt=start_datetime,
        end_dt=end_datetime,
        tz=tzinfo,
    ):
        item_list.append((timestamp, value))

    first_item = item_list[0]
    assert datetime.fromtimestamp(first_item[0], tz=tzinfo) == datetime(2022, 1, 10, 10, tzinfo=tzinfo)

    last_item = item_list[-1]
    assert datetime.fromtimestamp(last_item[0], tz=tzinfo) == datetime(2022, 1, 13, 13, tzinfo=tzinfo)

    # Difference more than 7 days
    start_datetime = datetime(2022, 1, 9, 10)
    end_datetime = datetime(2022, 1, 19, 20)
    tzinfo = timezone(timedelta(hours=6))
    item_list = []
    async for timestamp, value in _hourly_data(
        keyword='nft',
        start_dt=start_datetime,
        end_dt=end_datetime,
        tz=tzinfo,
    ):
        item_list.append((timestamp, value))

    first_item = item_list[0]
    assert datetime.fromtimestamp(first_item[0], tz=tzinfo) == datetime(2022, 1, 9, 10, tzinfo=tzinfo)

    last_item = item_list[-1]
    assert datetime.fromtimestamp(last_item[0], tz=tzinfo) == datetime(2022, 1, 19, 19, tzinfo=tzinfo)



@pytest.mark.asyncio
async def test_seven_days_data():
    lst = await alist(seven_days_data(
        keyword='nft',
        start_datetime=datetime(2020, 1, 1, 1),
        tzinfo=timezone(timedelta(hours=8)),
    ))

    assert lst[0][0] == datetime(2020, 1, 1, 1).timestamp()
    assert lst[-1][0] == datetime(2020, 1, 8, 0).timestamp()
