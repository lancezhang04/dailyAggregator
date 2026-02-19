# Daily Aggregator (Junes)

An intelligent executive assistant that manages tasks in Notion and sends daily reports via Gmail.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables in `.env`.
3. Run the local agent:
   ```bash
   python real-time.py
   ```
4. Run the Discord bot server:
   ```bash
   python server.py
   ```

## Discord Bot Configuration

To run the assistant 24/7 on a server using Discord, use `discord_server.py`. You will need:
- `DISCORD_BOT_TOKEN`: Obtain from the Discord Developer Portal.
- `DISCORD_AUTHORIZED_USER_ID`: Your Discord User ID (enable Developer Mode to copy it) to restrict access.
