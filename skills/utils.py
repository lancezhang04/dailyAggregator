from datetime import datetime
from zoneinfo import ZoneInfo

import os


def get_current_time() -> str:
    local_time = datetime.now(ZoneInfo(os.environ["LOCAL_TIMEZONE"]))
    return local_time.strftime("%Y-%m-%d %H:%M:%S")
