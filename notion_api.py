import os

from notion_client import Client

from task import NotionTask

client = Client(auth=os.environ["NOTION_TOKEN"])


def add_notion_page(task: NotionTask):
    client.pages.create(
        parent={"database_id": os.environ["NOTION_DATABASE_ID"]},
        properties=task.to_notion_properties(),
        icon={"type": "emoji", "emoji": "🤖"},
    )
