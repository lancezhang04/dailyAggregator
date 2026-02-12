import os
from dotenv import load_dotenv

from recorder import AudioRecorder
from apis.openai_api import OpenAIClient
from apis.notion_api import NotionClient
from apis.gmail_api import GmailClient
from task_aggregator import TaskAggregator


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
        else:
            print("\nError: REPORT_RECIPIENT_EMAIL not set in .env")
    except Exception as e:
        print(f"Error in task aggregation/emailing: {e}")


def main():
    load_dotenv()

    # Choose which function to test/run
    # record_and_add_task()
    aggregate_and_email_tasks()


if __name__ == "__main__":
    main()
