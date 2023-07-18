import aiohttp
import asyncio
import json
import logging
import os
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
FORM_URL = os.getenv("FORM_URL")
FORM_FIELD_IDS = json.loads(os.getenv("FORM_FIELD_IDS"))
USER_NAME_MAPPING = json.loads(os.getenv("USER_NAME_MAPPING"))

user_sessions = {}

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to RedhillAirconBot! Send /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("List of commands:\n/help - Show available commands\n/on - Start timer\n/off - End timer")

async def submit_google_form(user_name, start_time, end_time):
    start_hour = start_time.tm_hour
    start_minute = start_time.tm_min
    start_day = start_time.tm_mday
    start_month = start_time.tm_mon
    start_year = start_time.tm_year
    end_hour = end_time.tm_hour
    end_minute = end_time.tm_min
    end_day = end_time.tm_mday
    end_month = end_time.tm_mon
    end_year = end_time.tm_year

    form_data = {
        FORM_FIELD_IDS["name"]: user_name,
        FORM_FIELD_IDS["start_time_hour"]: start_hour,
        FORM_FIELD_IDS["start_time_minute"]: start_minute,
        FORM_FIELD_IDS["start_date_year"]: start_year,
        FORM_FIELD_IDS["start_date_month"]: start_month,
        FORM_FIELD_IDS["start_date_day"]: start_day,
        FORM_FIELD_IDS["end_time_hour"]: end_hour,
        FORM_FIELD_IDS["end_time_minute"]: end_minute,
        FORM_FIELD_IDS["end_date_year"]: end_year,
        FORM_FIELD_IDS["end_date_month"]: end_month,
        FORM_FIELD_IDS["end_date_day"]: end_day,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(FORM_URL, data=form_data) as response:
            return response.status == 200

async def on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        await update.message.reply_text("You already have an active session.")
    else:
        user_sessions[user_id] = time.localtime()
        await update.message.reply_text("Timer started. Use /off to stop the timer.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        start_time = user_sessions[user_id]
        del user_sessions[user_id]
        end_time = time.localtime()
        user_name = USER_NAME_MAPPING.get(str(user_id), "Unknown")

        if user_name != "Unknown" and await submit_google_form(user_name, start_time, end_time):
          await update.message.reply_text("Form submitted successfully!")
        else:
          await update.message.reply_text("Failed to submit the form. Please try again.")
    else:
        await update.message.reply_text("You don't have an active session. Use /on to start the timer.")

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm sorry, I don't understand that command. Send /help to see available commands.")

# Start the Bot
def main():
    application = Application.builder().token(TOKEN).build()

    # On command: Answer
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("on", on_command))
    application.add_handler(CommandHandler("off", off_command))

    # On non command: Return error messsage
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    asyncio.run(application.run_polling(allowed_updates=Update.ALL_TYPES))


if __name__ == "__main__":
    main()
