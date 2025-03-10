import json
import logging
import os
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment variables.")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ✅ Initialize Telegram bot application
app = Application.builder().token(TOKEN).build()

# Dictionary to track mining sessions
mining_sessions = {}


async def ensure_bot_initialized():
    """Ensure the bot is properly initialized before processing updates."""
    if not app.running:
        logger.info("🚀 Initializing bot...")
        await app.initialize()
        await app.start()
        logger.info("✅ Bot initialized and started.")
    else:
        logger.info("✅ Bot is already initialized.")


# ✅ Handler for /start command
async def start(update: Update, context: CallbackContext):
    logger.info("✅ /start command received")
    if update.message:
        await update.message.reply_text(
            "Hello! I am Kubot AI, a revolutionary gamified AI reward system. \n"
            "Click /mine to earn ten tokens after 10 seconds! 🚀"
        )
    else:
        logger.error("⚠️ No message object in update!")


# ✅ Handler for /stop command
async def stop(update: Update, context: CallbackContext):
    logger.info("✅ /stop command received")
    if update.message:
        await update.message.reply_text("Always remember that Kubot AI is here to assist you. Have a great day!")
    else:
        logger.error("⚠️ No message object in update!")


# ✅ Handler for /mine command
async def mine(update: Update, context: CallbackContext):
    logger.info("✅ /mine command received")
    if update.message:
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name

        # Check if the user is already mining
        if user_id in mining_sessions:
            await update.message.reply_text(f"{first_name}, you are already mining! Please wait until your current session ends.")
            return

        # Start mining session
        mining_sessions[user_id] = datetime.now()
        logger.info(f"⛏️ {first_name} started mining at {mining_sessions[user_id]}")
        await update.message.reply_text(
            f"⛏️ {first_name}, your mining session has started! You will mine for 10 seconds. "
            f"I will notify you when it's time to claim your rewards."
        )

        # Schedule the end of the mining session (10 seconds for testing)
        asyncio.create_task(end_mining_session(user_id, first_name, update.message.chat_id))
    else:
        logger.error("⚠️ No message object in update!")


async def end_mining_session(user_id: int, first_name: str, chat_id: int):
    """End the mining session after 10 seconds and notify the user."""
    logger.info(f"⏳ Waiting for 10 seconds to end mining session for {first_name}...")
    await asyncio.sleep(10)  # Wait for 10 seconds (for testing)

    if user_id in mining_sessions:
        # Calculate rewards (example: 10 tokens)
        rewards = 10
        logger.info(f"✅ Mining session ended for {first_name}. Sending rewards...")
        await app.bot.send_message(
            chat_id=chat_id,
            text=f"⛏️ {first_name}, your mining session has ended! You have earned {rewards} tokens. "
                 f"Use /mine to start mining again."
        )
        del mining_sessions[user_id]  # Remove the session
    else:
        logger.error(f"❌ No mining session found for user {user_id} ({first_name})")


# ✅ Handler for text messages (echo)
async def echo(update: Update, context: CallbackContext):
    logger.info(f"✅ Received message: {update.message.text}")
    if update.message:
        await update.message.reply_text(update.message.text)
    else:
        logger.error("⚠️ No message object in update!")


# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("mine", mine))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


@method_decorator(csrf_exempt, name='dispatch')  # ✅ Prevent 403 Forbidden
class TelegramWebhookView(View):
    """Handles incoming updates from Telegram via webhook."""

    async def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            logger.info(f"📩 Received Telegram update: {json.dumps(data, indent=2)}")

            # ✅ Ensure the bot is initialized before processing updates
            await ensure_bot_initialized()

            if not app.running:
                logger.error("❌ Bot is still not initialized!")
                return JsonResponse({"error": "Bot initialization failed"}, status=500)

            update = Update.de_json(data, app.bot)

            # ✅ Process update inside an async function
            await app.process_update(update)

            return JsonResponse({"status": "ok"}, status=200)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return JsonResponse({"error": "Internal Server Error"}, status=500)