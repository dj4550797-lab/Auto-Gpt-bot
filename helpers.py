import time
import requests
import info
from database import db_client
from cachetools import TTLCache
from Script import script

rate_limit_cache = TTLCache(maxsize=10000, ttl=60)

def is_admin(user_id):
    return user_id in info.ADMIN_IDS

def check_rate_limit(user_id):
    count = rate_limit_cache.get(user_id, 0)
    if count >= 10:
        return False
    rate_limit_cache[user_id] = count + 1
    return True

def generate_short_link(long_url):
    try:
        res = requests.get(f"{info.SHORTENER_API_URL}?api={info.SHORTENER_API_TOKEN}&url={long_url}")
        data = res.json()
        if data.get("status") == "success":
            return data.get("shortenedUrl")
    except Exception as e:
        print(f"Shortener error: {e}")
    return long_url

async def verify_access(update, context):
    user_id = update.effective_user.id
    user = db_client.get_user(user_id)
    
    if not user:
        await update.message.reply_text("🔒 You must register first. Use /register")
        return False
        
    if user.get("is_banned"):
        if user.get("ban_until") and time.time() > user.get("ban_until"):
            db_client.update_user(user_id, {"is_banned": False, "ban_until": None})
        else:
            await update.message.reply_text("🚫 You are banned from using this bot.")
            return False

    if not user.get("is_premium"):
        verified_until = user.get("verified_until", 0)
        if time.time() > verified_until:
            verify_url = f"https://t.me/{context.bot.username}?start=verify_{user_id}_{int(time.time())}"
            short_url = generate_short_link(verify_url)
            await update.message.reply_text(
                script.VERIFY_TXT.format(short_url=short_url),
                parse_mode="Markdown", disable_web_page_preview=True
            )
            return False
            
    return True