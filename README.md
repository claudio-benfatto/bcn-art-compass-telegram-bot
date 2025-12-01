## BCN Art Compass Telegram Bot (MVP)

This is a minimal Telegram bot frontend for the BCN Art Compass AI orchestrator.
It forwards user messages to the existing `/chat` HTTP endpoint and returns
the model's response back to the user in Telegram.

### Requirements

- Python 3.12+
- `uv` as dependency manager
- A running BCN Art Compass API (locally or in Cloud Run) exposing:
  - `POST /chat` with JSON body: `{"user_id": "...", "message": "..."}`.

### Setup

1. **Clone this repo or open the `bcn-art-compass-telegram-bot` folder.**

2. **Install dependencies with `uv`:**

```bash
cd /Users/claudio.benfatto/bcn-art-compass-telegram-bot
uv sync
```

3. **Create a Telegram bot token:**

- Talk to `@BotFather` in Telegram.
- Create a new bot and copy the HTTP API token.

4. **Configure environment variables (.env):**

Create a `.env` file in this folder (you can start from `.env.example`):

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
BCN_API_BASE_URL=http://localhost:8000    # or your Cloud Run URL

# Optional: logging level for the bot (DEBUG, INFO, WARNING, ERROR)
BCN_BOT_LOG_LEVEL=INFO
```

For Cloud Run, set `BCN_API_BASE_URL` to your service URL, e.g.:

```env
BCN_API_BASE_URL=https://bcn-art-compass-xxxx-uc.a.run.app
```

### Run the bot locally

```bash
cd /Users/claudio.benfatto/bcn-art-compass-telegram-bot
uv run python bot.py
```

Then talk to your bot in Telegram. Messages will be routed to the orchestrator
using your Telegram user identity as `user_id`.


