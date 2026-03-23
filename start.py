from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
import time

# Local imports from the project structure
import info
from database import db_client
from Script import script

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    - Sends the main welcome menu.
    - Processes verification deeplinks.
    """
    user = update.effective_user
    args = context.args
    
    # Check if the user is coming from a verification link
    if args and args[0].startswith("verify_"):
        try:
            # Format: verify_{user_id}_{timestamp}
            parts = args[0].split("_")
            if len(parts) == 3 and int(parts[1]) == user.id:
                # Grant 24-hour access
                db_client.update_user(user.id, {"verified_until": time.time() + 86400}) 
                await update.message.reply_text(
                    "✅ **Verification Successful!**\n\nYou now have full access for the next 24 hours."
                )
            else:
                await update.message.reply_text("⚠️ Invalid or expired verification link.")
        except (ValueError, IndexError):
             await update.message.reply_text("⚠️ Invalid verification link format.")
        return # Stop further processing after handling the link

    # Main Keyboard Layout
    keyboard = [
        [InlineKeyboardButton("📥 ADD ME TO GROUP", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📢 HELP", callback_data="help"), InlineKeyboardButton("📖 ABOUT", callback_data="about")],
        [InlineKeyboardButton("⭐ TOP SEARCHING", callback_data="top_search"), InlineKeyboardButton("💎 UPGRADE", callback_data="upgrade")],
        [InlineKeyboardButton("🧠 Change Model", callback_data="change_model"), InlineKeyboardButton("🗑 Reset Chat", callback_data="reset_chat")],
        [InlineKeyboardButton("🤖 MORE BOTS", url=info.MORE_BOTS_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Welcome Message Caption
    caption = script.START_TXT.format(name=user.first_name)
    
    # Send Welcome Message (with image if available)
    if info.WELCOME_IMAGE_URL:
        try:
            await update.message.reply_photo(
                photo=info.WELCOME_IMAGE_URL,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception:
            # Fallback to text if image fails to send
            await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            caption,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def button_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all callback queries from the inline buttons."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    data = query.data
    
    # Edit the message caption for info buttons
    if data == "help":
        await query.edit_message_caption(caption=script.HELP_TXT, parse_mode="Markdown")
    elif data == "about":
        await query.edit_message_caption(caption=script.ABOUT_TXT, parse_mode="Markdown")
    elif data == "top_search":
        await query.edit_message_caption(caption=script.TOP_SEARCH_TXT, parse_mode="Markdown")
        
    # Handle functional buttons
    elif data == "reset_chat":
        if 'chat_history' in context.user_data:
            context.user_data['chat_history'] = []
            await query.message.reply_text("🗑️ Chat history has been successfully cleared!")
        else:
            await query.message.reply_text("ℹ️ No chat history found to clear.")
            
    elif data == "change_model":
        model_buttons = [
            [InlineKeyboardButton(f"🤖 {model_name}", callback_data=f"set_{key}")]
            for key, model_name in info.MODELS.items()
        ]
        await query.message.reply_text("✨ Select your desired AI Model:", reply_markup=InlineKeyboardMarkup(model_buttons))
        
    # Handle model selection
    elif data.startswith("set_model_"):
        model_key = data.replace("set_", "")
        if model_key in info.MODELS:
            selected_model_name = info.MODELS[model_key]
            db_client.update_user(query.from_user.id, {"selected_model": selected_model_name})
            await query.edit_message_text(f"✅ AI Model has been switched to **{selected_model_name}**.", parse_mode="Markdown")
        else:
            await query.edit_message_text("❌ Error: Model not found.")

# Define the handlers to be imported by bot.py
start_handler = CommandHandler("start", start)
callback_handler = CallbackQueryHandler(button_callbacks, pattern="^(help|about|top_search|reset_chat|change_model|set_model_)")