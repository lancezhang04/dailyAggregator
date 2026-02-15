import os
import asyncio
import discord
from discord.ext import commands
import logging
import json
import datetime
from datetime import date
from dotenv import load_dotenv

# Import existing clients and skills
from apis.openai_api import OpenAIClient
import skills

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Constants
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
AUTHORIZED_USER_IDS = os.getenv("DISCORD_AUTHORIZED_USER_ID", "").split(",")
AUTHORIZED_USER_IDS = [int(i.strip()) for i in AUTHORIZED_USER_IDS if i.strip()]

# Initialize OpenAI Client
openai_client = OpenAIClient()


# Load tools and instructions
def load_agent_config():
    with open("tools.json", "r") as f:
        raw_tools = json.load(f)

    # Restructure tools for Chat Completions API
    tools = []
    for tool in raw_tools:
        if "type" in tool and tool["type"] == "function":
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            tools.append(formatted_tool)
        else:
            tools.append(tool)

    with open("AGENTS.md", "r") as f:
        instructions = f.read()

    # Replace placeholder
    current_date = datetime.datetime.now()
    instructions = instructions.replace(
        "{{today}}",
        f"{current_date.strftime('%Y-%m-%d')}, {current_date.strftime('%A')}",
    )
    return tools, instructions


# Global config state
TOOLS, INSTRUCTIONS = load_agent_config()
LAST_CONFIG_UPDATE = date.today()


def refresh_config_if_needed():
    """Updates the global instructions if the day has changed."""
    global TOOLS, INSTRUCTIONS, LAST_CONFIG_UPDATE
    today = date.today()
    if today != LAST_CONFIG_UPDATE:
        logging.info(f"Day changed to {today}. Refreshing agent configuration...")
        TOOLS, INSTRUCTIONS = load_agent_config()
        LAST_CONFIG_UPDATE = today

        # Update instructions in existing conversation histories
        for user_id in conversation_history:
            if (
                conversation_history[user_id]
                and conversation_history[user_id][0]["role"] == "system"
            ):
                conversation_history[user_id][0]["content"] = INSTRUCTIONS


# Simple in-memory conversation history: {user_id: [messages]}
conversation_history = {}

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def handle_tool_call(name, arguments):
    """Executes the corresponding skill based on the tool name."""
    logging.info(f"Executing tool: {name} with arguments: {arguments}")

    if name == "shutdown_agent":
        return "Junes is always active on the server, but tell Lance goodbye!"

    if name in skills.SKILLS_MAP:
        skill_func = skills.SKILLS_MAP[name]
        try:
            if asyncio.iscoroutinefunction(skill_func):
                return await skill_func(**arguments)
            else:
                return skill_func(**arguments)
        except Exception as e:
            logging.error(f"Error executing skill {name}: {e}")
            return f"Error executing skill {name}: {str(e)}"
    else:
        return f"Error: Unknown tool {name}"


async def process_response(message, user_text: str):
    refresh_config_if_needed()
    user_id = message.author.id

    if AUTHORIZED_USER_IDS and user_id not in AUTHORIZED_USER_IDS:
        await message.channel.send("Sorry, I am a private assistant.")
        return

    # Initialize history if not present
    if user_id not in conversation_history:
        conversation_history[user_id] = [{"role": "system", "content": INSTRUCTIONS}]

    # Add user message to history
    conversation_history[user_id].append({"role": "user", "content": user_text})

    # Keep history manageable (last 20 messages)
    if len(conversation_history[user_id]) > 21:
        conversation_history[user_id] = [
            conversation_history[user_id][0]
        ] + conversation_history[user_id][-20:]

    try:
        async with message.channel.typing():
            # Call OpenAI
            response = openai_client.client.chat.completions.create(
                model=openai_client.model,
                messages=conversation_history[user_id],
                tools=TOOLS,
                tool_choice="auto",
            )

            response_message = response.choices[0].message

            # Handle tool calls
            if response_message.tool_calls:
                conversation_history[user_id].append(response_message)

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    result = await handle_tool_call(function_name, function_args)

                    conversation_history[user_id].append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(result),
                        }
                    )

                # Get final response after tool execution
                second_response = openai_client.client.chat.completions.create(
                    model=openai_client.model,
                    messages=conversation_history[user_id],
                )
                final_text = second_response.choices[0].message.content
                conversation_history[user_id].append(
                    {"role": "assistant", "content": final_text}
                )
                await message.channel.send(final_text)
            else:
                final_text = response_message.content
                conversation_history[user_id].append(
                    {"role": "assistant", "content": final_text}
                )
                await message.channel.send(final_text)

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.channel.send(f"Oops, I ran into a bit of a snag: {str(e)}")


@bot.event
async def on_ready():
    print(f"Junes has logged in as {bot.user} (Discord)")


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Handle text messages
    if message.content:
        await process_response(message, message.content)

    # Handle voice messages or audio attachments
    elif message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and (
                attachment.content_type.startswith("audio/")
                or attachment.filename.endswith((".mp3", ".wav", ".ogg", ".m4a"))
            ):
                async with message.channel.typing():
                    temp_file = f"temp_{attachment.filename}"
                    await attachment.save(temp_file)
                    try:
                        # Transcribe audio
                        transcription = openai_client.transcribe_audio(temp_file)
                        logging.info(f"Transcription: {transcription}")
                        # Process as text
                        await process_response(message, transcription)
                    finally:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                break  # Only process one audio file per message


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment.")
        exit(1)

    bot.run(DISCORD_BOT_TOKEN)
