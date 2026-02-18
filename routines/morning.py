import sys
import os
import asyncio
from pathlib import Path
import datetime

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from dotenv import load_dotenv
from apis.openai_api import OpenAIClient
from apis.gmail_api import GmailClient
from apis.notion_api import NotionClient
from skills.utils import get_next_24hr_weather_forecast, get_local_now
from blueprint_routine.blueprint_skills import gather_routine_information


async def send_discord_message(token, user_id, content):
    """Sends a message to a Discord user via DM."""
    import discord

    intents = discord.Intents.default()
    async with discord.Client(intents=intents) as client:
        try:
            # We need to login and start the client to be able to fetch user
            # But discord.Client as a context manager handles cleanup.
            # However, fetch_user needs the client to be logged in.

            # Use a task to handle the actual work once ready
            ready_event = asyncio.Event()

            @client.event
            async def on_ready():
                ready_event.set()

            # Start client in a task
            client_task = asyncio.create_task(client.start(token))

            # Wait for ready
            try:
                await asyncio.wait_for(ready_event.wait(), timeout=30)
                user = await client.fetch_user(int(user_id))
                if user:
                    full_content = f"<@{user_id}>\n\n{content}"
                    await user.send(full_content)
                    print(f"Discord message sent to {user.name}.")
                else:
                    print(f"Error: Could not find Discord user with ID {user_id}")
            except asyncio.TimeoutError:
                print("Error: Discord client timed out waiting to be ready.")
            except Exception as e:
                print(f"Error during Discord message sending: {e}")
            finally:
                # Stop the client
                await client.close()
                await client_task
        except Exception as e:
            print(f"Error in send_discord_message: {e}")


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
    today = get_local_now().strftime("%Y-%m-%d, %A")

    system_prompt = (
        "You are Junes, a loyal, casual, and highly capable personal assistant. "
        "You've been with your boss for a long time, so you speak in a relaxed, warm, and relatively informal tone. "
        "You are sending a morning text to your boss. "
        "Do no use Markdown syntax. "
        "Your goal is to provide a brief update on the weather, today's routine (skincare, supplements, workout), "
        "and any TRULY URGENT tasks from Notion. "
        "Urgent tasks are usually those due today or overdue, and impending tasks that require lots of work and foresight. "
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
    subject = f"Junes' note for {today}"
    gmail_client.send_email(to=recipient_email, subject=subject, content=note_content)

    print(f"Morning routine email sent to {recipient_email}.")

    # 6. Send Discord Message
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    discord_user_id = os.getenv("DISCORD_AUTHORIZED_USER_ID")
    if discord_token and discord_user_id:
        import asyncio

        asyncio.run(send_discord_message(discord_token, discord_user_id, note_content))
    else:
        print(
            "Skipping Discord message: DISCORD_BOT_TOKEN or DISCORD_AUTHORIZED_USER_ID not set."
        )


if __name__ == "__main__":
    main()
