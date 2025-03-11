import json
import logging
import os
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from telegram.error import NetworkError
from asyncio import TimeoutError
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

# Dictionary to store user rewards
user_rewards = {}


async def ensure_bot_initialized():
    """Ensure the bot is properly initialized before processing updates."""
    try:
        if not app.running:
            logger.info("🚀 Initializing bot...")
            await app.initialize()
            await app.start()
            logger.info("✅ Bot initialized and started.")
        else:
            logger.info("✅ Bot is already initialized.")
    except NetworkError as e:
        logger.error(f"🌐 Network error while initializing bot: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during bot initialization: {e}")


# ✅ Handler for /start command
async def start(update: Update, context: CallbackContext):
    logger.info("✅ /start command received")
    if update.message:
        try:
            await update.message.reply_text(
                "Hello! I am Kubot AI, a revolutionary gamified AI reward system.\n"
                "Click /mine to earn fifty Kubot tokens after 60 seconds! 🚀"
            )
        except (NetworkError, TimeoutError) as e:
            logger.error(f"🌐 Network error while sending start message: {e}")
            await update.message.reply_text(
                "Hello! I am Kubot AI, a revolutionary gamified AI reward system.\n"
                "Click /mine to earn fifty Kubot tokens after 60 seconds! 🚀"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            
    else:
        logger.error("⚠️ No message object in update!")


# ✅ Handler for /stop command
async def stop(update: Update, context: CallbackContext):
    logger.info("✅ /stop command received")
    if update.message:
        user_id = update.message.from_user.id
        try:
            mining_sessions.pop(user_id, None)
            await update.message.reply_text("Always remember that Kubot AI is here to assist you. Have a great day!")
        except (NetworkError, TimeoutError) as e:
            logger.error(f"🌐 Network error while sending stop message: {e}")
            mining_sessions.pop(user_id, None)
            await update.message.reply_text("Always remember that Kubot AI is here to assist you. Have a great day!")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
    else:
        logger.error("⚠️ No message object in update!")


# ✅ Handler for /mine command
async def mine(update: Update, context: CallbackContext):
    if update.message:
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name

        if user_id in mining_sessions:
            try:
                await update.message.reply_text(
                    f"{first_name}, you are already mining! Please wait until your current session ends."
                )
            except (NetworkError, TimeoutError) as e:
                logger.error(f"🌐 Network error while sending mining warning: {e}")
                await mine(update, context)
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
            return

        mining_sessions[user_id] = datetime.now()
        try:
            await update.message.reply_text(
                f"⛏️ {first_name}, your mining session has begun! You'll be mining for 60 seconds. ⏳"
            )
            # Start mining process
            asyncio.create_task(finish_mining(user_id, first_name, update))
        except (NetworkError, TimeoutError) as e:
            await update.message.reply_text(
                f"⛏️ {first_name}, your mining session has begun! You'll be mining for 60 seconds. ⏳"
            )
            # logger.error(f"🌐 Network error while sending mining start message: {e}")
            await finish_mining(user_id, first_name, update)
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")

        


async def finish_mining(user_id, first_name, update: Update):
    """Handles mining completion after 60 seconds"""
    print("let's get started")
    await asyncio.sleep(10)
    new_reward = 50
    total_reward = user_rewards.get(user_id, 0) + new_reward
    user_rewards[user_id] = total_reward

    try:
        await update.message.reply_text(
            f"{first_name}, your mining session has ended! You have earned {new_reward} tokens.\n"
            f"💰 Your total balance is now {total_reward} tokens.\n"
            f"Click on the /mine button continue mining ⛏️"
        )
    except (NetworkError, TimeoutError) as e:
        logger.error(f"🌐 Network error while sending mining result: {e}")
        await finish_mining(user_id, first_name, update)
    except Exception as e:
        logger.error(f"❌ Unexpected error sending mining result: {e}")

    mining_sessions.pop(user_id, None)
    
    
async def check_balance(update: Update, context: CallbackContext):
    """Checks the balance of a user"""
    if update.message:
        user_id = update.message.from_user.id
        first_name = update.message.from_user.first_name
        
        try:
            reward = user_rewards[user_id]
        except KeyError:
            await update.message.reply_text(
                f"{first_name},\n\n"
                f"💰 Your have 0 Kubot tokens currently.\n"
                f"Click on the /mine button start mining ⛏️"
            )

        try:
            await update.message.reply_text(
                f"{first_name},\n\n"
                f"💰 Your total balance is now {reward} tokens.\n"
                f"Click on the /mine button continue mining ⛏️"
            )
        except (NetworkError, TimeoutError) as e:
            logger.error(f"🌐 Network error while sending mining result: {e}")
            await update.message.reply_text(
                f"{first_name},\n\n"
                f"💰 Your total balance is now {reward} tokens.\n"
                f"Click on the /mine button continue mining ⛏️"
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error checking balance: {e}")



# ✅ Handler for text messages (echo)
async def echo(update: Update, context: CallbackContext):
    logger.info(f"✅ Received message: {update.message.text}")
    if update.message:
        try:
            await update.message.reply_text(update.message.text)
        except (NetworkError, TimeoutError) as e:
            logger.error(f"🌐 Network error while echoing message: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
    else:
        logger.error("⚠️ No message object in update!")


# Register handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("mine", mine))
app.add_handler(CommandHandler("balance", check_balance))
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

        except (NetworkError, TimeoutError) as e:
            logger.error(f"🌐 Network error while processing update: {e}")
            return JsonResponse({"error": "Network error, please try again later"}, status=503)

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return JsonResponse({"error": "Internal Server Error"}, status=500)
