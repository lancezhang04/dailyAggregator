from datetime import date
import os

from models.task import NotionTask


def transcribe_audio(client):
    audio_file = open("output.wav", "rb")

    return client.audio.transcriptions.create(
        model="gpt-audio",
        file=audio_file,
    ).text


def extract_task_from_text(user_input: str, client) -> NotionTask:
    completion = client.responses.parse(
        model=os.environ["OPENAI_MODEL"],
        instructions=f"You are a helpful assistant that extracts task details. Today is {date.today()}",
        input=user_input,
        text_format=NotionTask,
    )
    return completion.output_parsed
