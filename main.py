import os

from dotenv import load_dotenv
from openai import OpenAI

from notion_api import add_notion_page
from testing.recording_test import record_audio
from testing.whisper_test import extract_task_from_text, transcribe_audio

load_dotenv()


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
record_audio()
transcription = transcribe_audio(openai_client)
print(f"transcription: {transcription}")
task = extract_task_from_text(transcription, openai_client)

print("adding notion page...")
add_notion_page(task)
print("complete, page created:")
