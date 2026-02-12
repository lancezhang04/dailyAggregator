from typing import Optional
from datetime import date

from pydantic import BaseModel, Field


class NotionTask(BaseModel):
    task_name: str = Field(description='A concise title for the task')
    status: str = Field(description="Should be 'Not started', 'In progress', or 'Done'")
    task_types: list[str] = Field(description="Should be 'Personal', 'Entertainment', 'Logistics', 'Learning', 'Misc', 'Shopping', 'Health', or 'Work'. All 'Work' tasks should be strictly related to my firm.")
    due_date: Optional[date] = Field(description='The deadline for the task in YYYY-MM-DD form. Optional field.')

    def to_notion_properties(self):
        properties = {
            'Task': {
                'title': [{'text': {'content': self.task_name}}],
            },
            'Status': {
                'status': {'name': self.status},
            },
            'Type': {
                'multi_select': [{'name': t} for t in self.task_types],
            }
        }

        if self.due_date:
            properties['Due Date'] = {
                'date': {'start': self.due_date.isoformat()},
            }
        return properties


if __name__ == '__main__':
    task = NotionTask(
        task_name='Test task',
        status='Not started',
        task_types=['Logistics'],
        due_date=date(2026, 2, 15),
    )
    print(task.to_notion_properties())
