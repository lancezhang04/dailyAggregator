from .notion_skills import (
    record_and_add_task,
    add_new_task,
    get_pending_tasks,
    mark_task_as_done,
)
from .email_skills import aggregate_and_email_tasks
from .system_skills import shutdown_agent, toggle_voice_mode
from .utils import get_current_time, get_next_24hr_weather_forecast
from blueprint_routine.blueprint_skills import gather_routine_information

# Global mapping of skill name to function
SKILLS_MAP = {
    "add_new_task": add_new_task,
    "get_pending_tasks": get_pending_tasks,
    "mark_task_as_done": mark_task_as_done,
    "aggregate_and_email_tasks": aggregate_and_email_tasks,
    "shutdown_agent": shutdown_agent,
    "toggle_voice_mode": toggle_voice_mode,
    "get_current_time": get_current_time,
    "gather_routine_information": gather_routine_information,
    "record_and_add_task": record_and_add_task,
    "get_next_24hr_weather_forecast": get_next_24hr_weather_forecast,
}

__all__ = [
    "add_new_task",
    "get_pending_tasks",
    "mark_task_as_done",
    "aggregate_and_email_tasks",
    "shutdown_agent",
    "toggle_voice_mode",
    "get_current_time",
    "gather_routine_information",
    "record_and_add_task",
    "SKILLS_MAP",
]
