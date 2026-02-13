import os
from notion_client import Client
from models.task import NotionTask


class NotionClient:
    def __init__(
        self, token: str = None, database_id: str = None, source_id: str = None
    ):
        self.token = token or os.getenv("NOTION_TOKEN")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        self.source_id = source_id or os.getenv("NOTION_SOURCE_ID")
        self.client = Client(auth=self.token)

    def add_task(self, task: NotionTask):
        return self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=task.to_notion_properties(),
            icon={"type": "emoji", "emoji": "🤖"},
        )

    def get_pending_tasks(self):
        """Fetches tasks that are not 'Done'."""
        results = self.client.data_sources.query(
            data_source_id=self.source_id,
            filter={"property": "Status", "status": {"does_not_equal": "Done"}},
        ).get("results", [])

        tasks = []
        for page in results:
            props = page.get("properties", {})
            task_name = ""
            if "Task" in props and props["Task"]["title"]:
                task_name = props["Task"]["title"][0]["text"]["content"]

            status = props.get("Status", {}).get("status", {}).get("name", "Unknown")

            task_types = []
            if "Type" in props:
                task_types = [t["name"] for t in props["Type"].get("multi_select", [])]

            due_date = None
            if "Due Date" in props and props["Due Date"].get("date"):
                due_date = props["Due Date"]["date"]["start"]

            tasks.append(
                {
                    "task_name": task_name,
                    "status": status,
                    "task_types": task_types,
                    "due_date": due_date,
                }
            )
        return tasks
