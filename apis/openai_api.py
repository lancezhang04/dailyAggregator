import os
from datetime import date
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from models.task import NotionTask

load_dotenv()


class OpenAIClient:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)

    def transcribe_audio(self, file_path: str):
        with open(file_path, "rb") as audio_file:
            return self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",  # As per original code
                file=audio_file,
            ).text

    def extract_task(self, text: str) -> NotionTask:
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": f"You are a helpful assistant that extracts task details. Today is {date.today()}",
            },
            {"role": "user", "content": text},
        ]
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=NotionTask,
        )
        return completion.choices[0].message.parsed

    def summarize_tasks(self, tasks: list[dict]) -> str:
        if not tasks:
            return "<h1>Daily Update</h1><p>You have no pending tasks at the moment. Enjoy your day!</p>"

        task_list_str = "\n".join(
            [
                f"- {t['task_name']} (Status: {t['status']}, Due: {t['due_date'] or 'N/A'}, Types: {', '.join(t['task_types'])})"
                for t in tasks
            ]
        )

        system_prompt = (
            "You are a highly capable executive assistant like Pepper Potts from Ironman. "
            "Your goal is to provide a concise, intelligent, and highly useful summary of your executive's pending tasks. "
            "Don't just list everything. Analyze the tasks and tell them exactly what they should focus on TODAY and what's most critical. "
            "Be brief, professional, and proactive. "
            "Format your response as clean HTML that will look great in Gmail (use headers, bullet points, and bold text as needed) with a blue and white color scheme. "
        )

        user_prompt = (
            f"Here are the current pending tasks:\n{task_list_str}\n\n"
            "Please provide an executive summary and priority focus for today."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = None,
        response_format: str = "mp3",
    ):
        """Generates speech from text using OpenAI TTS."""
        if voice is None:
            voice = os.getenv("OPENAI_VOICE_MODEL_LEGACY", "nova")

        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format=response_format,
        )
        response.write_to_file(output_path)
