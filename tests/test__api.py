from datetime import datetime, timezone, timedelta
from google_trends_api import _api
from google_trends_api import constants


async def test_get_cookies():
    cookies = await _api.get_cookies()
    assert isinstance(cookies, dict)
    assert cookies['NID']


async def test_get_widgets():
    widgets = await _api.get_widgets(
        'nft',
        timezone_offset=0,
        cookies=await _api.get_cookies(),
        time_range=constants.TimeRange.PAST_1D,
    )
    assert isinstance(widgets, list)
    assert widgets != []
    assert widgets[0] != []

    widgets = await _api.get_widgets(
        'nft',
        timezone_offset=0,
        cookies=await _api.get_cookies(),
        custom_time_range=(
            datetime.today() - timedelta(days=1),
            datetime.today()
        )
    )
    assert isinstance(widgets, list)
    assert widgets != []
    assert widgets[0] != []


async def test_interest_over_time():
    cookies = await _api.get_cookies()
    widgets = await _api.get_widgets(
        keyword='nft',
        timezone_offset=-480,
        cookies=cookies,
        time_range=constants.TimeRange.PAST_1D,
    )

    js = await _api.interest_over_time(
        cookies, widgets, timezone_offset=-480
    )
    timeline_data = js['default']['timelineData']

    assert isinstance(js, dict)
    assert isinstance(timeline_data, list)
    assert timeline_data != []


# async def test_interest_over_time():
#     hours = 8
#     tz_info = timezone(timedelta(hours=hours))
#     timezone_offset = -60 * hours
#
#     start_datetime = datetime(2022, 1, 25, hour=10, tzinfo=tz_info)
#     end_datetime = datetime(2022, 1, 26, hour=13, tzinfo=tz_info)
#
#     cookies = await _api.get_cookies()
#     hourly_data = await _api.get_hourly_data(
#         'nft',
#         cookies,
#         timezone_offset=timezone_offset,
#         start_datetime=datetime(2022, 1, 25, 10),
#         end_datetime=datetime(2022, 1, 26, 13),
#     )
#     trends_list = hourly_data['default']['timelineData']
#
#     first_item = trends_list[0]
#     dt = datetime.fromtimestamp(int(first_item['time']), tz=tz_info)
#     assert (start_datetime + timedelta(hours=hours)) == dt

    # last_item = trends_list[-1]
    # dt = datetime.fromtimestamp(int(last_item['time']), tz=tz_info)
    # assert (end_datetime + timedelta(hours=hours)) == dt
