from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes

import info
from database import db_client
from utils.logger import send_log
from Script import script
from plugins.start import start

# --- Plan Configuration ---
# Format: { 'callback_data': ('Display Name', 'price_in_rs', 'duration_in_days') }
PREMIUM_PLANS = {
    "plan_daily_20": ("☀️ Daily Pass", "20", 1),
    "plan_weekly_79": ("📅 Weekly Pass", "79", 7),
    "plan_monthly_199": ("🌙 Monthly Pass", "199", 30)
}

# --- Conversation States ---
UTR, SCREENSHOT = range(2)

async def show_premium_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the premium benefits and the list of available plans as buttons."""
    query = update.callback_query
    
    plan_buttons = []
    for key, (name, price, _) in PREMIUM_PLANS.items():
        plan_buttons.append([InlineKeyboardButton(f"{name} - ₹{price}", callback_data=key)])
    
    plan_buttons.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_start")])
    reply_markup = InlineKeyboardMarkup(plan_buttons)
    
    # Combine the info text and the plans text
    full_caption = script.PREMIUM_INFO_TXT + "\n" + script.PREMIUM_PLANS_TXT

    await query.edit_message_caption(
        caption=full_caption,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await query.answer()

async def select_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's plan selection, then shows payment details."""
    query = update.callback_query
    plan_key = query.data
    
    plan_name, amount, duration_days = PREMIUM_PLANS[plan_key]
    
    # Store the selected plan details for the payment submission step
    context.user_data['selected_plan'] = {
        'name': plan_name,
        'price': amount,
        'days': duration_days
    }
    
    await query.message.delete()
    
    text = script.UPGRADE_TXT.format(
        plan_name=plan_name,
        amount=amount,
        upi_id=info.UPI_ID
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data="upgrade")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if info.QR_IMAGE_URL:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=info.QR_IMAGE_URL,
            caption=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    await query.answer()

async def back_to_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Back' button by recreating the start menu."""
    query = update.callback_query
    await query.message.delete()
    # Call the original start function to show the main menu
    await start(update, context)
    await query.answer()

# --- Payment Submission (Now includes plan details) ---

async def start_payment_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the process to submit payment proof."""
    await update.message.reply_text("🧾 Please enter the 12-digit **UTR / Transaction ID** from your payment:", parse_mode="Markdown")
    return UTR

async def get_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['utr'] = update.message.text
    await update.message.reply_text("📸 Great! Now, please upload the **Payment Screenshot**:", parse_mode="Markdown")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id
    
    # Get plan details from user_data, with a fallback
    plan_info = context.user_data.get('selected_plan', {'name': 'Unknown Plan', 'price': 'N/A'})
    
    payment_data = {
        "user_id": user.id,
        "name": user.full_name,
        "utr": context.user_data.get('utr', 'N/A'),
        "screenshot": photo_file_id,
        "plan_name": plan_info['name'],
        "amount_paid": plan_info['price'],
        "status": "pending"
    }
    db_client.insert_payment(payment_data)
    
    await update.message.reply_text("✅ Payment submitted! An admin will review it shortly.")
    
    # Create a more detailed log message for admins
    log_text = (
        f"💰 **New Payment Submission**\n\n"
        f"**User:** {user.full_name} (`{user.id}`)\n"
        f"**Plan:** {plan_info['name']}\n"
        f"**Amount:** ₹{plan_info['price']}\n"
        f"**UTR:** `{context.user_data.get('utr', 'N/A')}`"
    )
    await send_log(context, log_text)
    
    admin_caption = f"{log_text}\n\nApprove with: `/premium {user.id} {plan_info.get('days', 30)}`"
    for admin_id in info.ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=photo_file_id, caption=admin_caption, parse_mode="Markdown")
        except Exception:
            await context.bot.send_message(admin_id, admin_caption, parse_mode="Markdown")
            
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Payment submission cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

# --- HANDLERS ---

# 1. User clicks "Upgrade" on the main menu -> show_premium_plans
premium_cb_handler = CallbackQueryHandler(show_premium_plans, pattern="^upgrade$")

# 2. User selects a specific plan -> select_plan_callback
plan_selection_cb_handler = CallbackQueryHandler(select_plan_callback, pattern="^plan_")

# 3. User clicks "Back to Main Menu" -> back_to_start_menu
back_to_start_cb_handler = CallbackQueryHandler(back_to_start_menu, pattern="^back_to_start$")

# 4. Handles the /submit_payment conversation
payment_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("submit_payment", start_payment_submission)],
    states={
        UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_utr)],
        SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
    },
    fallbacks=[CommandHandler("cancel", cancel_payment)],
    conversation_timeout=300
)