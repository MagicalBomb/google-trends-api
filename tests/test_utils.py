from datetime import datetime, timedelta
from google_trends_api import utils


def test_datetime_range():
    start_datetime = datetime(2020, 1, 1)
    end_datetime = datetime(2020, 1, 7)
    step = timedelta(days=4)

    datetime_list = list(utils.datetime_range(start_datetime, end_datetime, step, can_overflow=False))
    assert datetime_list == [
        datetime(2020, 1, 1),
        datetime(2020, 1, 5),
    ]

    datetime_list = list(utils.datetime_range(start_datetime, end_datetime, step, can_overflow=True))
    assert datetime_list == [
        datetime(2020, 1, 1),
        datetime(2020, 1, 5),
        datetime(2020, 1, 9),
    ]
