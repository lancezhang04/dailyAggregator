import os
from datetime import date

from notion_client import Client, APIResponseError, APIErrorCode
from dotenv import load_dotenv

from task import NotionTask


load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])

# list_users_response = notion.users.list()
# print(list_users_response)


def retrieve_current_tasks():
    try:
        return notion.data_sources.query(
            data_source_id=os.environ['NOTION_SOURCE_ID'],
            filter={
                'property': 'Status',
                'status': {
                    'does_not_equal': 'Done',
                }
            },
        )['results']
    except APIResponseError as error:
        if error.code == APIErrorCode.ObjectNotFound:
            print('no current tasks were found.')
        else:
            raise error


def get_task_title(task: dict):
    return task['properties']['Task']['title'][0]['plain_text']


# tasks = retrieve_current_tasks()
# print(f'{len(tasks)} current tasks were found.')
#
# for t in tasks:
#     print(get_task_title(t))


task = NotionTask(
task_name='Test task',
    status='Not started',
    task_types=['Logistics'],
    due_date=date(2026, 2, 15),
)

notion.pages.create(
    parent={'database_id': os.environ['NOTION_DATABASE_ID']},
    properties=task.to_notion_properties(),
    icon={'type': 'emoji', 'emoji': '🤖'},
)
