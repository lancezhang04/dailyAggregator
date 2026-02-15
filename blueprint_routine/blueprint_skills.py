import yaml
import datetime

ALLOWED_ROUTINE_CATEGORIES = ["supplements", "skincare", "workouts"]


def gather_routine_information(routine_type: str, day_idx: int = None) -> str:
    routine_type = routine_type.lower()
    if routine_type not in ALLOWED_ROUTINE_CATEGORIES:
        return f"{routine_type} is not a valid routine category. Choose from {', '.join(ALLOWED_ROUTINE_CATEGORIES)}"

    with open(f"blueprint_routine/{routine_type}.yaml", "r") as f:
        data = yaml.safe_load(f)

    content = data["main"]
    if day_idx is None:
        day_idx = datetime.date.today().weekday()
    if day_idx in data:
        content += "\n\n" + data[day_idx]
    return content


if __name__ == "__main__":
    print(gather_routine_information("supplements"))
