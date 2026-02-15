import os
from apis.gmail_api import GmailClient
from apis.notion_api import NotionClient
from apis.openai_api import OpenAIClient
from tools.task_aggregator import TaskAggregator


def aggregate_and_email_tasks():
    """Fetches pending tasks from Notion, summarizes them, and emails the report."""
    openai_client = OpenAIClient()
    notion_client = NotionClient()
    gmail_client = GmailClient()

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
