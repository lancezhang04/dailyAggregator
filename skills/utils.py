from datetime import datetime, date
from zoneinfo import ZoneInfo

import os
import requests


def get_local_now() -> datetime:
    """Returns the current datetime in the local timezone."""
    return datetime.now(ZoneInfo(os.environ.get("LOCAL_TIMEZONE", "UTC")))


def get_current_time() -> str:
    local_time = get_local_now()
    return local_time.strftime("%Y-%m-%d %H:%M:%S")


def get_next_24hr_weather_forecast() -> str:
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/forecast",
        params={
            "q": os.environ["OPERATING_CITY"],
            "appid": os.environ["OPENWEATHERMAP_API_KEY"],
            "units": "imperial",
        },
    )

    if response.status_code != 200:
        return "Error retrieving weather forecast."

    forecast_list = response.json()["list"][:8]
    intervals = []
    for entry in forecast_list:
        timestamp = datetime.fromtimestamp(entry["dt"]).strftime("%I %p").lstrip("0")
        temp = int(entry["main"]["temp"])
        desc = entry["weather"][0]["description"]
        intervals.append(f"{timestamp}: {temp}°F, {desc}")

    return f"24hr weather forecast for {os.environ['OPERATING_CITY']}:\n{' | '.join(intervals)}"


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print(get_next_24hr_weather_forecast())
