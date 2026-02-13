from apis.notion_api import NotionClient
from apis.openai_api import OpenAIClient
from apis.gmail_api import GmailClient


class TaskAggregator:
    def __init__(
        self,
        notion_client: NotionClient,
        openai_client: OpenAIClient,
        gmail_client: GmailClient,
    ):
        self.notion_client = notion_client
        self.openai_client = openai_client
        self.gmail_client = gmail_client

    def generate_report(self):
        """Fetches pending tasks and generates a professional summary."""
        print("Fetching pending tasks from Notion...")
        tasks = self.notion_client.get_pending_tasks()

        print(f"Found {len(tasks)} pending tasks. Generating summary...")
        summary = self.openai_client.summarize_tasks(tasks)

        return summary

    def email_report(self, to_email: str, summary: str):
        """Emails the summary."""
        print(f"Sending summary email to {to_email}...")
        subject = "Daily Task Summary & Next Steps"
        # Since summary is now HTML, we provide it as html_content.
        # We can use a simple text version for the plain content.
        plain_text = "Please enable HTML to view this report."
        self.gmail_client.send_email(
            to_email, subject, plain_text, html_content=summary
        )
        print("Email sent successfully.")
