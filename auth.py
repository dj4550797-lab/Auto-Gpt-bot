from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
import re
import info
from database import db_client
from utils.logger import send_log

# Conversation states
NAME, EMAIL, PHONE, DOB, PASSWORD = range(5)

async def start_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the registration process."""
    if db_client.get_user(update.effective_user.id):
        await update.message.reply_text("✅ You are already registered!")
        return ConversationHandler.END
        
    await update.message.reply_text("📝 Let's get you registered! First, what is your **Full Name**?", parse_mode="Markdown")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves name and asks for email."""
    context.user_data['reg_name'] = update.message.text
    await update.message.reply_text("📧 Great! Now, please enter your **Email Address**:", parse_mode="Markdown")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validates email and asks for phone."""
    email = update.message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text("❌ That email format looks incorrect. Please try again:")
        return EMAIL
    context.user_data['reg_email'] = email
    await update.message.reply_text("📱 Next, what is your **Phone Number**? (e.g., 91xxxxxxxxxx)", parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validates phone and asks for DOB."""
    phone = update.message.text
    if not phone.isdigit() or len(phone) < 7:
        await update.message.reply_text("❌ That doesn't look like a valid phone number. Please enter digits only:")
        return PHONE
    context.user_data['reg_phone'] = phone
    await update.message.reply_text("📅 Almost done! Please enter your **Date of Birth** (DD/MM/YYYY):", parse_mode="Markdown")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves DOB and asks for password."""
    context.user_data['reg_dob'] = update.message.text
    await update.message.reply_text("🔑 Finally, create a **Password** for your account:", parse_mode="Markdown")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves password, creates user, and ends conversation."""
    user = update.effective_user
    user_data = {
        "user_id": user.id,
        "name": context.user_data['reg_name'],
        "email": context.user_data['reg_email'],
        "phone": context.user_data['reg_phone'],
        "dob": context.user_data['reg_dob'],
        "password": update.message.text, # In a real production scenario, HASH this password.
        "verified_until": 0,
        "is_premium": False,
        "premium_expiry": None,
        "is_banned": False,
        "ban_until": None,
        "selected_model": info.MODELS["model_1"]
    }
    db_client.create_user(user_data)
    
    await update.message.reply_text("✅ **Registration Complete!**\n\nYou can now use all the features of FLIXORA AI. Start by sending me a message!")
    await send_log(context, f"👤 **New Registration**\nName: {user_data['name']}\nID: `{user.id}`\nEmail: {user_data['email']}")
    
    # Clean up temporary data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the registration process."""
    await update.message.reply_text("Registration has been cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

auth_handler = ConversationHandler(
    entry_points=[CommandHandler("register", start_register)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
    },
    fallbacks=[CommandHandler("cancel", cancel_reg)],
    conversation_timeout=300 # 5 minutes
)