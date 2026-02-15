import sys
import os
from pathlib import Path
import datetime

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from dotenv import load_dotenv
from apis.openai_api import OpenAIClient
from apis.gmail_api import GmailClient
from apis.notion_api import NotionClient
from skills.utils import get_next_24hr_weather_forecast
from blueprint_routine.blueprint_skills import gather_routine_information


def main():
    # Load environment variables from the root directory
    load_dotenv(dotenv_path=root_dir / ".env")

    openai_client = OpenAIClient()
    gmail_client = GmailClient(
        credentials_path=str(root_dir / "playground/gmail_api/credentials.json"),
        token_path=str(root_dir / "playground/gmail_api/token.json"),
    )
    notion_client = NotionClient()

    recipient_email = os.getenv("REPORT_RECIPIENT_EMAIL")
    if not recipient_email:
        print("Error: REPORT_RECIPIENT_EMAIL not found in environment.")
        return

    # 1. Gather Weather
    weather_info = get_next_24hr_weather_forecast()

    # 2. Gather Routine
    supplements = gather_routine_information("supplements")
    skincare = gather_routine_information("skincare")
    workouts = gather_routine_information("workouts")

    # 3. Gather Notion Tasks
    tasks = notion_client.get_pending_tasks()

    # 4. Generate Message with OpenAI
    today = datetime.date.today().strftime("%Y-%m-%d, %A")

    system_prompt = (
        "You are Junes, a loyal, casual, and highly capable personal assistant. "
        "You've been with your boss for a long time, so you speak in a relaxed, warm, and slightly informal tone. "
        "You are writing a morning note to your boss. "
        "Your goal is to provide a brief update on the weather, today's routine (skincare, supplements, workout), "
        "and any TRULY URGENT tasks from Notion. "
        "Urgent tasks are usually those due today or overdue, but use your judgment. "
        "Do NOT list every task. Just the ones that need immediate attention. "
        "Keep it concise, friendly, and human. Not like a mechanical report."
    )

    user_data = f"""
Today's Date: {today}

Weather Forecast:
{weather_info}

Routine for Today:
- Supplements: {supplements}
- Skincare: {skincare}
- Workout: {workouts}

Pending Notion Tasks:
{tasks}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_data},
    ]

    response = openai_client.client.chat.completions.create(
        model=openai_client.model,
        messages=messages,
    )

    note_content = response.choices[0].message.content

    # 5. Send Email
    subject = f"Good morning! Your note for {today}"
    gmail_client.send_email(to=recipient_email, subject=subject, content=note_content)

    print(f"Morning routine email sent to {recipient_email}.")


if __name__ == "__main__":
    main()
