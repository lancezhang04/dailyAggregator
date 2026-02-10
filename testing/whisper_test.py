import os

from openai import OpenAI

# TODO: horrible coding practice, but oh well
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
audio_file = open('output.wav', 'rb')

transcription = client.audio.transcriptions.create(
    model='gpt-4o-transcribe',
    file=audio_file,
)

print(f'transcription result: {transcription}')
