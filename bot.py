import logging
import os
from typing import Final

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()


def _load_config() -> tuple[str, str, int]:
    """Load bot configuration from environment/.env."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    api_base = os.getenv("BCN_API_BASE_URL", "http://localhost:8000")
    log_level_name = os.getenv("BCN_BOT_LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Configure it in the environment or .env file."
        )

    return token, api_base, log_level


TELEGRAM_BOT_TOKEN: Final[str]
BCN_API_BASE_URL: Final[str]
_token, _base_url, _log_level = _load_config()
TELEGRAM_BOT_TOKEN = _token
BCN_API_BASE_URL = _base_url

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=_log_level
)
logger = logging.getLogger(__name__)


async def call_bcn_api(user_id: str, message: str) -> str:
    """Call BCN Art Compass /chat endpoint and return the response text."""
    url = f"{BCN_API_BASE_URL.rstrip('/')}/chat"
    payload = {"user_id": user_id, "message": message}

    timeout = httpx.Timeout(60.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # FastAPI response model is {"response": "...", "correlation_id": "..."}
            return data.get("response") or "No response from BCN Art Compass."
        except Exception as e:  # noqa: BLE001
            logger.exception("Error calling BCN Art Compass API: %s", e)
            return (
                "I couldn't reach the BCN Art Compass backend right now. "
                "Please try again in a moment."
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    first_name = user.first_name if user and user.first_name else "there"
    msg = (
        f"Hi {first_name}! I'm your BCN Art Compass bot.\n\n"
        "Tell me what kind of art or cultural events you're interested in, "
        "and I'll ask the BCN Art Compass AI to help you discover exhibitions "
        "and galleries in Barcelona."
    )
    await update.message.reply_text(msg)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    msg = (
        "You can send me any message like:\n"
        "- \"I love sculpture and don't like video art\"\n"
        "- \"What art exhibitions are happening this weekend?\"\n"
        "- \"I'm in Gràcia, suggest something nearby\"\n\n"
        "I'll forward it to BCN Art Compass and reply with its recommendations."
    )
    await update.message.reply_text(msg)


def _telegram_user_id(update: Update) -> str:
    """Derive a stable user_id for BCN Art Compass from Telegram update."""
    if update.effective_user and update.effective_user.username:
        return f"tg_{update.effective_user.username}"
    if update.effective_user and update.effective_user.id:
        return f"tg_id_{update.effective_user.id}"
    if update.effective_chat and update.effective_chat.id:
        return f"tg_chat_{update.effective_chat.id}"
    return "tg_unknown"


def _format_for_telegram(text: str) -> str:
    """Format the API response text for better Telegram display.
    
    Converts Markdown-style formatting to clean plain text with emojis.
    """
    import re
    
    # Replace markdown bold with emoji highlights
    text = re.sub(r'\*\*([^*]+)\*\*', r'🎨 \1', text)
    
    # Add emojis to common fields
    text = re.sub(r'(Why you[^:]*:)', r'💡 \1', text)
    text = re.sub(r'(When:)', r'📅 \1', text)
    text = re.sub(r'(Where:)', r'📍 \1', text)
    text = re.sub(r'(Location:)', r'📍 \1', text)
    text = re.sub(r'(Price:)', r'💰 \1', text)
    text = re.sub(r'(More Info:)', r'🔗 \1', text)
    
    # Clean up numbered lists with better spacing
    text = re.sub(r'^(\d+)\.\s+', r'\n\1️⃣ ', text, flags=re.MULTILINE)
    
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', r'\n\n', text)
    
    return text.strip()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward any text message to BCN Art Compass and reply with its answer."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user_id = _telegram_user_id(update)

    # Optional typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    logger.info("Calling BCN API for user %s with message: %s", user_id, text[:50])
    response_text = await call_bcn_api(user_id=user_id, message=text)
    logger.info("Received response of length %d", len(response_text))

    # Format for Telegram with emojis and clean layout
    formatted_text = _format_for_telegram(response_text)

    # Telegram has message length limits; keep it simple for now.
    if len(formatted_text) > 4000:
        formatted_text = formatted_text[:3996] + "..."

    # Send as plain text (already formatted nicely)
    await update.message.reply_text(formatted_text)
    logger.info("Message sent successfully")


def main() -> None:
    """Entry point to start the Telegram bot."""
    logger.info("Starting BCN Art Compass Telegram bot...")
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # run_polling manages the asyncio event loop internally; no need for asyncio.run
    app.run_polling()


if __name__ == "__main__":
    main()


