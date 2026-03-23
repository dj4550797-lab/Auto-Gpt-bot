from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import time
from datetime import datetime
import info
from database import db_client
from utils.logger import send_log
from utils.helpers import is_admin as is_admin_check

async def admin_command(func):
    """Decorator to check for admin privileges."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not is_admin_check(update.effective_user.id):
            await update.message.reply_text("⛔ You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@admin_command
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "No reason provided."
        db_client.update_user(user_id, {"is_banned": True, "ban_until": None})
        await update.message.reply_text(f"✅ User `{user_id}` has been permanently banned.", parse_mode="Markdown")
        await send_log(context, f"🔨 **User Banned**\nAdmin: `{update.effective_user.id}`\nTarget: `{user_id}`\nReason: {reason}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/ban <user_id> [reason]`")

@admin_command
async def give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        expiry = time.time() + (days * 86400)
        db_client.update_user(user_id, {"is_premium": True, "premium_expiry": expiry})
        await update.message.reply_text(f"✅ Premium granted to `{user_id}` for {days} days.", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"💎 Congratulations! You have been granted Premium status for {days} days.")
        await send_log(context, f"💎 **Premium Granted**\nTarget: `{user_id}`\nDays: {days}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/premium <user_id> <days>`")

@admin_command
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        db_client.update_payment(user_id, "approved")
        # Default premium on approval: 30 days
        await give_premium(update, context) 
        await update.message.reply_text(f"✅ Payment from `{user_id}` has been approved.", parse_mode="Markdown")
        await send_log(context, f"✅ **Payment Approved**\nAdmin: `{update.effective_user.id}`\nUser: `{user_id}`")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/approve <user_id>`")

@admin_command
async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "Your submitted proof was not valid."
        db_client.update_payment(user_id, "rejected")
        await update.message.reply_text(f"❌ Payment from `{user_id}` has been rejected.", parse_mode="Markdown")
        await context.bot.send_message(user_id, f"❌ Your payment submission was rejected.\nReason: {reason}")
        await send_log(context, f"❌ **Payment Rejected**\nAdmin: `{update.effective_user.id}`\nUser: `{user_id}`")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/reject <user_id> [reason]`")

@admin_command
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.reply_to_message
    if not message:
        await update.message.reply_text("Reply to a message to broadcast it.")
        return
        
    users = db_client.get_all_users()
    success, failed = 0, 0
    status_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    for user in users:
        try:
            await context.bot.copy_message(chat_id=user['user_id'], from_chat_id=update.message.chat_id, message_id=message.message_id)
            success += 1
            await asyncio.sleep(0.05) # To avoid flood limits
        except Exception:
            failed += 1
    await status_msg.edit_text(f"✅ Broadcast complete.\nSent: {success}\nFailed: {failed}")

@admin_command
async def get_users_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db_client.get_all_users()
    total = len(users)
    premium = sum(1 for u in users if u.get('is_premium'))
    banned = sum(1 for u in users if u.get('is_banned'))
    text = f"📊 **Bot Stats**\n\nTotal Users: `{total}`\nPremium Users: `{premium}`\nBanned Users: `{banned}`"
    await update.message.reply_text(text, parse_mode="Markdown")

admin_handlers = [
    CommandHandler("ban", ban_user),
    CommandHandler("premium", give_premium),
    CommandHandler("approve", approve_payment),
    CommandHandler("reject", reject_payment),
    CommandHandler("broadcast", broadcast),
    CommandHandler("users", get_users_info)
    # Add other admin commands here in the same format
]