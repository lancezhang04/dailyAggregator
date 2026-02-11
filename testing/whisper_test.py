from datetime import date
import os

from dotenv import load_dotenv
from openai import OpenAI

from task import NotionTask


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
audio_file = open('output.wav', 'rb')

transcription = client.audio.transcriptions.create(
    model='gpt-4o-transcribe',
    file=audio_file,
)

print(f'transcription result: {transcription}')


def extract_task_from_text(user_input: str) -> NotionTask:
    completion = client.responses.parse(
        model=os.environ['OPENAI_MODEL'],
        instructions=f'You are a helpful assistant that extracts task details. Today is {date.today()}',
        input=user_input,
        text_format=NotionTask,
    )
    return completion.output_parsed


print(extract_task_from_text(transcription.text))
