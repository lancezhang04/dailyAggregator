import asyncio
import base64
import json
import time
import datetime
import os

try:
    import pyaudio
except ImportError:
    pyaudio = None
    print("Warning: pyaudio not found. Audio input/output will not work.")

try:
    import websockets
    from websockets.asyncio.client import connect
except ImportError:
    websockets = None
    connect = None
    print("Warning: websockets not found. Connection to OpenAI will fail.")

from dotenv import load_dotenv

from skills import *

# Load environment variables
load_dotenv()

# Realtime API configuration
MODEL = "gpt-4o-realtime-preview"
URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"

# Audio configuration
CHANNELS = 1
RATE = 24000
CHUNK_SIZE = 1024


def load_config():
    """Loads tool definitions and agent instructions."""
    try:
        with open("tools.json", "r") as f:
            tools = json.load(f)
        with open("AGENTS.md", "r") as f:
            instructions = f.read()

        # Replace placeholders
        current_date = datetime.datetime.now()
        instructions = instructions.replace(
            "{{today}}",
            f"{current_date.strftime('%Y-%m-%d')}, {current_date.strftime('%A')}",
        )
        return tools, instructions
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return [], "You are a helpful assistant."


async def send_audio(ws, stream, state):
    """Continuously reads audio from the microphone and sends it to OpenAI."""
    if not stream:
        print("Audio stream not initialized. Speech input will not be sent.")
        return

    print("Microphone active. Speak now...")
    try:
        last_instructions_update = datetime.date.today()

        while not state.get("should_shutdown"):
            # Check if we need to update instructions (day change)
            today = datetime.date.today()
            if today != last_instructions_update:
                print(
                    f"\n--- Day changed to {today}. Updating session instructions... ---"
                )
                _, instructions = load_config()
                session_update = {
                    "type": "session.update",
                    "session": {
                        "instructions": instructions,
                    },
                }
                await ws.send(json.dumps(session_update))
                last_instructions_update = today

            # Read audio data from stream
            data = await asyncio.to_thread(
                stream.read, CHUNK_SIZE, exception_on_overflow=False
            )
            if not data:
                await asyncio.sleep(0.01)
                continue

            # Skip sending if we are currently playing audio or just finished playing
            # This prevents a feedback loop where the agent hears its own voice.
            if state.get("is_playing") or (
                time.time() - state.get("last_output_at", 0) < 0.5
            ):
                continue

            base64_audio = base64.b64encode(data).decode("utf-8")
            audio_event = {"type": "input_audio_buffer.append", "audio": base64_audio}
            await ws.send(json.dumps(audio_event))
    except Exception as e:
        print(f"Error sending audio: {e}")


async def handle_events(ws, stream, state):
    """Receives events from the WebSocket and handles them (audio output, tool calls)."""
    try:
        while not state.get("should_shutdown"):
            message = await ws.recv()
            event = json.loads(message)
            event_type = event.get("type")
            # print(f"DEBUG: Received event: {event_type}") # Uncomment for full event logging

            if event_type == "response.audio.delta":
                # Play back audio response
                if stream and state.get("is_response_active"):
                    audio_content = base64.b64decode(event["delta"])
                    try:
                        state["is_playing"] = True
                        await asyncio.to_thread(stream.write, audio_content)
                        state["last_output_at"] = time.time()
                        state["is_playing"] = False
                    except Exception as e:
                        state["is_playing"] = False
                        print(f"\nError writing to audio stream: {e}")
                continue

            elif event_type == "response.audio_transcript.delta":
                delta = event.get("delta")
                if delta:
                    print(delta, end="", flush=True)
                continue

            elif event_type == "response.text.delta":
                delta = event.get("delta")
                if delta:
                    print(delta, end="", flush=True)
                continue

            elif event_type in ["input_audio_buffer.append", "rate_limits.updated"]:
                continue

            elif event_type == "response.done":
                state["is_response_active"] = False
                response = event.get("response", {})
                if response.get("status") == "failed":
                    error_details = response.get("status_details", {}).get("error", {})
                    error_msg = error_details.get("message", "Unknown error")
                    print(f"\nResponse failed: {error_msg}")

                # Check for tool calls
                output_items = response.get("output", [])
                for item in output_items:
                    if item.get("type") == "function_call":
                        await handle_tool_call(ws, item, state)

            elif event_type == "error":
                error_data = event.get("error", {})
                if (
                    isinstance(error_data, dict)
                    and error_data.get("code") == "response_cancel_not_active"
                ):
                    # Ignore this common race condition error
                    pass
                else:
                    state["is_response_active"] = False
                    print(f"\nAPI Error: {error_data}")

            elif event_type == "input_audio_buffer.speech_started":
                print("\nSpeech detected...")
                if state.get("is_response_active"):
                    # Send cancel event to server to stop current response generation
                    await ws.send(json.dumps({"type": "response.cancel"}))
                    state["is_response_active"] = False
                    print("[Interrupted]")

            elif event_type == "response.cancel.done":
                state["is_response_active"] = False
                print("\nResponse cancelled.")

            elif event_type == "input_audio_buffer.speech_stopped":
                print("Speech stopped.")

            elif event_type == "input_audio_buffer.committed":
                print("Audio buffer committed.")

            elif event_type == "response.created":
                state["is_response_active"] = True
                print("\nAgent is thinking...")

            elif event_type == "response.audio_transcript.done":
                print()  # New line after agent transcript is complete

            elif event_type == "response.text.done":
                print()

            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = event.get("transcript", "")
                if transcript:
                    print(f"\nYou: {transcript}", flush=True)

    except Exception as e:
        print(f"Error handling events: {e}")


async def handle_tool_call(ws, item, state):
    """Executes a tool call and sends the result back to the API."""
    call_id = item.get("call_id")
    name = item.get("name")
    arguments_raw = item.get("arguments", "{}")
    try:
        arguments = json.loads(arguments_raw)
    except json.JSONDecodeError:
        print(f"Error decoding arguments for {name}: {arguments_raw}")
        arguments = {}

    print(f"\n[Tool Call] {name}: {arguments}")

    # Map tool names to actual functions in skills
    skill_map = SKILLS_MAP

    if name in skill_map:
        try:
            # Execute the skill
            if asyncio.iscoroutinefunction(skill_map[name]):
                result = await skill_map[name](**arguments)
            else:
                result = skill_map[name](**arguments)

            if name == "shutdown_agent":
                state["should_shutdown"] = True

            # Send the output back
            output_event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result),
                },
            }
            await ws.send(json.dumps(output_event))

            # Request a response from the model after the tool output
            await ws.send(json.dumps({"type": "response.create"}))

        except Exception as e:
            print(f"Error executing tool {name}: {e}")
            error_event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps({"error": str(e)}),
                },
            }
            await ws.send(json.dumps(error_event))
            await ws.send(json.dumps({"type": "response.create"}))
    else:
        print(f"Unknown tool: {name}")


async def run_agent():
    """Main entry point for the Realtime Agent."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        return

    if connect is None:
        print("Error: websockets library is required.")
        return

    tools, instructions = load_config()

    # Initialize PyAudio
    input_stream = None
    output_stream = None
    p = None

    if pyaudio:
        try:
            p = pyaudio.PyAudio()
            input_stream = p.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            output_stream = p.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
            )
        except Exception as e:
            print(f"Error initializing audio devices: {e}")
            print("Running in text-only mode (if supported by your setup).")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    print(f"Connecting to OpenAI Realtime API ({MODEL})...")
    try:
        async with connect(URL, additional_headers=headers) as ws:
            print("Connected.")

            # 1. Initialize Session
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": instructions,
                    "voice": os.environ["OPENAI_VOICE_MODEL"],
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                    },
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.9,
                },
            }
            await ws.send(json.dumps(session_update))

            # 2. Run send and receive loops concurrently
            state = {
                "is_response_active": False,
                "last_output_at": 0,
                "is_playing": False,
                "should_shutdown": False,
            }
            await asyncio.gather(
                send_audio(ws, input_stream, state),
                handle_events(ws, output_stream, state),
            )
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if input_stream:
            try:
                input_stream.stop_stream()
                input_stream.close()
            except:
                pass
        if output_stream:
            try:
                output_stream.stop_stream()
                output_stream.close()
            except:
                pass
        if p:
            try:
                p.terminate()
            except:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
