# Google-Trends-API

Async Python wrapper for Google Trends API.

# Install
```
pip install git+https://github.com/MagicalBomb/google-trends-api.git
```

# Usage
```python
import asyncio
import datetime
from google_trends_api import GoogleTrendsApi

async def main():    
    api = GoogleTrendsApi(proxies='http://localhost:1234')
    async for timestamp, trends_value in api.get_hourly_data(
        keyword='bitcoin',
        start_datetime=datetime.datetime(2022, 1, 10, 11),
        end_datetime=datetime.datetime(2022, 1, 20, 12),
    ):
        print(timestamp, trends_value)
    await api.aclose()

asyncio.run(main())
```