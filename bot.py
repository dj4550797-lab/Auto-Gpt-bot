import logging
import logging.config
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes

# Import configurations and database client
import info
from database import db_client

# Import all handlers from the plugins directory
from plugins.start import start_handler, callback_handler
from plugins.auth import auth_handler
from plugins.ai_chat import chat_handler
from plugins.premium import (
    premium_cb_handler,
    plan_selection_cb_handler,
    back_to_start_cb_handler,
    payment_conv_handler
)
from plugins.admin import admin_handlers

# Setup logging from the configuration file for a cleaner output
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

# --- Main Application Setup ---

# Initialize the python-telegram-bot Application
# We use a post_init function to set up the webhook asynchronously
async def post_init(application: Application):
    """
    Sets the webhook after the application has been initialized.
    This is the recommended approach for PTB v20+ with webhooks.
    """
    if info.WEBHOOK_URL:
        webhook_url = f"{info.WEBHOOK_URL}/{info.BOT_TOKEN}"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook successfully set to {webhook_url}")
    else:
        logger.warning("⚠️ No WEBHOOK_URL found in .env. Bot will not start with a webhook.")

ptb_app = Application.builder().token(info.BOT_TOKEN).post_init(post_init).build()

# --- Register Handlers ---
logger.info("Registering handlers...")

# Core Handlers
ptb_app.add_handler(start_handler)
ptb_app.add_handler(auth_handler)

# Main Menu Callback Handlers (from start.py)
ptb_app.add_handler(callback_handler)

# Premium Menu Handlers (from premium.py)
ptb_app.add_handler(premium_cb_handler)
ptb_app.add_handler(plan_selection_cb_handler)
ptb_app.add_handler(back_to_start_cb_handler)
ptb_app.add_handler(payment_conv_handler)

# Admin Handlers (from admin.py)
for handler in admin_handlers:
    ptb_app.add_handler(handler)

# AI Chat Handler (must be last among MessageHandlers to not override others)
ptb_app.add_handler(chat_handler)

# --- Global Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs errors caused by updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    # Optionally, inform the user that an error occurred
    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="An unexpected error occurred. The developers have been notified."
        )

ptb_app.add_error_handler(error_handler)

# --- Scheduled Jobs ---
async def auto_cleanup_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Runs periodically to clean up expired premium memberships and bans.
    """
    import time
    now = time.time()
    logger.info("Running auto cleanup job...")
    
    users = db_client.get_all_users()
    for user in users:
        # Check for expired premium
        if user.get("is_premium") and user.get("premium_expiry") and now > user.get("premium_expiry"):
            db_client.update_user(user["user_id"], {"is_premium": False, "premium_expiry": None})
            try:
                await context.bot.send_message(user["user_id"], "⚠️ Your Premium subscription has expired. Use /upgrade to renew!")
            except Exception as e:
                logger.warning(f"Could not notify user {user['user_id']} of premium expiry: {e}")

        # Check for expired temporary bans
        if user.get("is_banned") and user.get("ban_until") and now > user.get("ban_until"):
            db_client.update_user(user["user_id"], {"is_banned": False, "ban_until": None})
            logger.info(f"Auto-unbanned user {user['user_id']}.")

ptb_app.job_queue.run_repeating(auto_cleanup_job, interval=3600, first=30) # Run every hour

# --- Flask Web Server for Webhook ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    """A simple endpoint to confirm the bot is running."""
    return "FLIXORA AI Bot is up and running."

@flask_app.route(f'/{info.BOT_TOKEN}', methods=['POST'])
async def webhook():
    """
    This endpoint receives the updates from Telegram.
    It's the entry point for all user interactions when deployed.
    """
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, ptb_app.bot)
        await ptb_app.process_update(update)
        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return "Error", 500

async def main():
    """Initializes the application and its webhook."""
    logger.info("Initializing PTB application...")
    await ptb_app.initialize()
    logger.info("PTB application initialized.")

if __name__ == '__main__':
    # This setup ensures that the bot's async components are initialized
    # before the synchronous Flask/Gunicorn server starts listening for requests.
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(main())
    else:
        loop.run_until_complete(main())
    
    # When running locally without Docker/Gunicorn for testing, you might uncomment the following lines:
    # if not info.WEBHOOK_URL:
    #     logger.info("Starting bot in polling mode for local testing...")
    #     ptb_app.run_polling()
    # else:
    #     logger.info(f"Starting Flask server on port {info.PORT} for webhook...")
    #     flask_app.run(host="0.0.0.0", port=info.PORT)
    
    logger.info("Setup complete. Gunicorn will now take over to run the Flask app.")