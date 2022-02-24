import datetime


class API:
    EXPLORE = 'https://trends.google.com/trends/api/explore'
    TRENDS_OVER_TIME = 'https://trends.google.com/trends/api/widgetdata/multiline'


class WidgetId:
    TIME_SERIES = 'TIMESERIES'
    GEO_MAP = 'GEO_MAP'
    RELATED_TOPICS = 'RELATED_TOPICS'
    RELATED_QUERIES = 'RELATED_QUERIES'


class Frequency:
    DAILY = 'daily'
    HOURLY = 'hourly'


class TimeRange:
    PAST_1H = 'now 1-H'
    PAST_4H = 'now 4-H'
    PAST_1D = 'now 1-d'
    PAST_7D = 'now 7-d'
    PAST_30D = 'now 30-d'
    PAST_90D = 'now 90-d'
    PAST_12M = 'today 12-m'
    PAST_5Y = 'today 5-y'
    FROM_2004_TO_NOW = 'all'
