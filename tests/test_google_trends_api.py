from datetime import datetime, timezone, timedelta

import pytest

from google_trends_api import hourly_data


@pytest.mark.asyncio
async def test_hourly_data():
    start_datetime = datetime(2022, 1, 10, 10)
    end_datetime = datetime(2022, 1, 13, 14)
    tzinfo = timezone(timedelta(hours=6))
    item_list = []
    async for timestamp, value in hourly_data(
        keyword='nft',
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        tzinfo=tzinfo,
    ):
        item_list.append((timestamp, value))

    first_item = item_list[0]
    assert datetime.fromtimestamp(first_item[0], tz=tzinfo) == datetime(2022, 1, 10, 10, tzinfo=tzinfo)

    last_item = item_list[-1]
    assert datetime.fromtimestamp(last_item[0], tz=tzinfo) == datetime(2022, 1, 13, 14, tzinfo=tzinfo)
