import os

from apis.gmail_api import GmailClient
from apis.notion_api import NotionClient
from apis.openai_api import OpenAIClient
from tools.recorder import AudioRecorder
from tools.task_aggregator import TaskAggregator


def record_and_add_task():
    """Records audio, transcribes it, extracts a task, and adds it to Notion."""
    recorder = AudioRecorder()
    openai_client = OpenAIClient()
    notion_client = NotionClient()

    print("--- New Task Recording ---")
    try:
        audio_file = recorder.record()
        if audio_file:
            transcription = openai_client.transcribe_audio(audio_file)
            print(f"Transcription: {transcription}")

            task = openai_client.extract_task(transcription)
            print(f"Extracted Task: {task.task_name}")

            notion_client.add_task(task)
            print("Task added to Notion.")
    except Exception as e:
        print(f"Error in task recording/adding: {e}")


def add_new_task(
    task_name: str,
    status: str = "Not started",
    task_types: list = None,
    due_date: str = None,
    description: str = None,
):
    """Directly adds a new task to Notion. Useful for agents that have already parsed the user's intent."""
    notion_client = NotionClient()
    from models.task import NotionTask
    from datetime import datetime

    print(f"\n--- Adding New Task: {task_name} ---")
    if description:
        print(f"Description: {description}")
    try:
        parsed_due_date = None
        if due_date:
            parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        task = NotionTask(
            task_name=task_name,
            status=status,
            task_types=task_types or ["Misc"],
            due_date=parsed_due_date,
            description=description,
        )
        notion_client.add_task(task)
        print("Task added to Notion.")
        return f"Successfully added task: {task_name}"
    except Exception as e:
        print(f"Error adding task: {e}")
        return f"Error adding task: {str(e)}"


def aggregate_and_email_tasks():
    """Fetches pending tasks from Notion, summarizes them, and emails the report."""
    openai_client = OpenAIClient()
    notion_client = NotionClient()
    gmail_client = GmailClient()  # Mandatory now

    print("\n--- Daily Task Aggregation ---")
    try:
        aggregator = TaskAggregator(notion_client, openai_client, gmail_client)
        report = aggregator.generate_report()

        print("\nExecutive Summary:")
        print("-" * 20)
        print(report)
        print("-" * 20)

        recipient = os.getenv("REPORT_RECIPIENT_EMAIL")
        if recipient:
            aggregator.email_report(recipient, report)
            return f"Daily summary sent to {recipient}."
        else:
            print("\nError: REPORT_RECIPIENT_EMAIL not set in .env")
            return "Error: REPORT_RECIPIENT_EMAIL not set in .env"
    except Exception as e:
        print(f"Error in task aggregation/emailing: {e}")
        return f"Error in task aggregation/emailing: {str(e)}"


def get_pending_tasks():
    """Fetches all tasks that are not 'Done' from Notion."""
    notion_client = NotionClient()
    print("\n--- Fetching Pending Tasks ---")
    try:
        tasks = notion_client.get_pending_tasks()
        print(f"Found {len(tasks)} pending tasks.")
        return tasks
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return f"Error fetching tasks: {str(e)}"


def mark_task_as_done(page_id: str, task_name: str = None):
    """Marks a task as 'Done' in Notion using its page ID."""
    notion_client = NotionClient()
    print(f"\n--- Marking Task as Done: {task_name or page_id} ---")
    try:
        notion_client.update_task_status(page_id, "Done")
        name_display = f"'{task_name}'" if task_name else f"ID: {page_id}"
        print(f"Task {name_display} marked as Done.")
        return f"Successfully marked {name_display} as Done."
    except Exception as e:
        print(f"Error marking task as done: {e}")
        return f"Error marking task as done: {str(e)}"


def shutdown_agent():
    """Signals the agent to shut down and close the session."""
    print("\n--- Shutting Down Agent ---")
    return "Shutting down. Goodbye!"
