import json
import logging
import os
import asyncio
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from telegram.error import NetworkError
from asyncio import TimeoutError
from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputFile
from .models import Wallet, Referral
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, Updater
from asgiref.sync import sync_to_async

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


async def start(update: Update, context: CallbackContext):
    logger.info("✅ /start command received")
    
    WEB_BOT_URL = "https://kubotai.vercel.app/"
    IMAGE_PATH = "kubot_ai/static/kubot.png"

    if not update.message:
        logger.error("⚠️ No message object in update!")
        return

    user = update.message.from_user
    user_id = update.message.from_user.id
    username = user.username

    print(f"Username: {username}")

    # ✅ Extract referral ID from arguments (if available)
    args = context.args
    referral_id = args[0] if args else None

    if referral_id:
        print(f"Welcome! Your referral ID is: {referral_id}")

        # Check if the user already has a wallet
        try:
            existing_wallet = await sync_to_async(Wallet.objects.get, thread_sensitive=True)(user=username)
            await update.message.reply_text("You already have a wallet!")
            return  

        except Wallet.DoesNotExist:
            existing_wallet = None

        referred_user = None 

        if referral_id:
            try:
                referred_user = await sync_to_async(Wallet.objects.get, thread_sensitive=True)(referral_id=referral_id)

                # Check if a referral already exists
                referral_exists = await sync_to_async(Referral.objects.filter(referred_user__user=username).exists)()
                if referral_exists:
                    await update.message.reply_text("You have already been referred!")
                    return  # Stop execution if referral already exists

            except Wallet.DoesNotExist:
                await update.message.reply_text("Referral ID is invalid!")
                return  # Stop execution if referral ID is invalid

        # ✅ Create new wallet for user
        new_wallet = await sync_to_async(Wallet.objects.create, thread_sensitive=True)(user=username,id=user_id)

        # ✅ Create referral only if there is a valid referred user
        if referred_user:
            await sync_to_async(Referral.objects.create, thread_sensitive=True)(
                referrer=referred_user,
                referral_id=referral_id,
                referred_user=new_wallet
            )

            # ✅ Update balance of the referring user
            referred_user.balance += 5
            await sync_to_async(referred_user.save, thread_sensitive=True)()

            await update.message.reply_text("Referral successful! 🎉")

        else:
            await update.message.reply_text("Welcome! No referral ID detected.")
    else:
        try:
            new_wallet = await sync_to_async(Wallet.objects.create, thread_sensitive=True)(user=username, id=user_id)
        except Exception as e:
            print("User already registered")
            print(f"Error: {e}")
            ...

    # ✅ Create inline button for the web app
    keyboard = [[InlineKeyboardButton("🚀 Open Mini App", web_app=WebAppInfo(url=WEB_BOT_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ✅ Send welcome image with button
    try:
        if os.path.exists(IMAGE_PATH):  
            with open(IMAGE_PATH, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption="🌟 Welcome to Kubot AI! 🌟\nKubotAI combines cryptocurrency gamification with task-based rewards.",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text("⚠️ An error occurred. Please try again later.")

    except Exception as e:
        logger.error(f"❌ Error sending image: {e}")
        await update.message.reply_text("⚠️ An error occurred while sending the welcome image.")
          
          

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


def index_view(request):
    return render(request, "index.html")