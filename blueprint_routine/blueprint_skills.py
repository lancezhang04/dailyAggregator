import yaml
import datetime
from pathlib import Path
import os
from zoneinfo import ZoneInfo

ALLOWED_ROUTINE_CATEGORIES = ["supplements", "skincare", "workouts"]


def gather_routine_information(routine_type: str, day_of_week: str = None) -> str:
    routine_type = routine_type.lower()
    if routine_type not in ALLOWED_ROUTINE_CATEGORIES:
        return f"{routine_type} is not a valid routine category. Choose from {', '.join(ALLOWED_ROUTINE_CATEGORIES)}"

    base_path = Path(__file__).parent
    with open(base_path / f"{routine_type}.yaml", "r") as f:
        data = yaml.safe_load(f)

    content = data["main"]

    if day_of_week is None:
        local_timezone = os.environ.get("LOCAL_TIMEZONE", "UTC")
        day_of_week = (
            datetime.datetime.now(ZoneInfo(local_timezone)).strftime("%A").lower()
        )
    else:
        day_of_week = day_of_week.lower()

    if day_of_week in data:
        content += "\n\n" + data[day_of_week]
    return content


if __name__ == "__main__":
    print(gather_routine_information("supplements"))
