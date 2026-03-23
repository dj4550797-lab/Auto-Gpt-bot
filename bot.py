import os, asyncio, time, re, httpx
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from motor.motor_asyncio import AsyncIOMotorClient
from aiohttp import web

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URL = os.environ.get("MONGO_URL", "")
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split()]
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))
S_URL = os.environ.get("SHORTENER_URL", "")
S_API = os.environ.get("SHORTENER_API", "")
PORT = os.environ.get("PORT", "10000") # Render default

THINK_STICKER = "CAACAgIAAxkBAAMIacD-Ra4_z1RuU2JTyYBeqq-qHrUAAvUAA_cCyA9HRphh0VDIsR4E"

# Temporary storage for registration states
USER_STATES = {} 

# --- DB SETUP ---
db = AsyncIOMotorClient(MONGO_URL)["FlixoraGPT"]
users_col = db["users"]

app = Client("FlixoraGPT", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER (FIXES RENDER PORT ERROR) ---
async def web_server():
    server = web.Application()
    server.add_routes([web.get('/', lambda r: web.Response(text="Flixora AI is Online"))])
    runner = web.AppRunner(server); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(PORT)).start()
    print(f"Web server started on port {PORT}")

# --- HELPERS ---
async def get_verify_link(user_id):
    base = f"https://t.me/{app.me.username}?start=verify_{user_id}"
    async with httpx.AsyncClient() as c:
        res = await c.get(f"https://{S_URL}/api?api={S_API}&url={base}")
        return res.json().get("shortenedUrl", base)

# --- REGISTRATION & LOGIN LOGIC ---
@app.on_message(filters.command("start") & filters.private)
async def start(c, m):
    uid = m.from_user.id
    user = await users_col.find_one({"_id": uid})

    # Handle Verification Link
    if len(m.command) > 1 and m.command[1].startswith("verify_"):
        await users_col.update_one({"_id": uid}, {"$set": {"last_verified": time.time()}})
        return await m.reply_text("✅ Verification Successful! Access granted for 24h.")

    # Check if user is registered
    if not user or not user.get("email"):
        USER_STATES[uid] = "ASK_NAME"
        return await m.reply_text("👋 **Welcome to Flixora AI!**\n\nPlease register to continue.\n\n**Step 1:** What is your Full Name?")

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Select AI", callback_data="model_menu"), InlineKeyboardButton("👤 My Account", callback_data="status")],
        [InlineKeyboardButton("🆘 Get Help", callback_data="ask_help"), InlineKeyboardButton("🔗 Refer", callback_data="refer")],
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{c.me.username}?startgroup=true")]
    ])
    await m.reply_text(f"✨ **Welcome Back, {user['name']}!**\nHow can Flixora assist you today?", reply_markup=btn)

@app.on_message(filters.text & filters.private)
async def handle_input(c, m):
    uid = m.from_user.id
    state = USER_STATES.get(uid)

    # Registration Wizard
    if state == "ASK_NAME":
        USER_STATES[uid] = {"name": m.text, "state": "ASK_EMAIL"}
        await m.reply_text(f"Nice to meet you, {m.text}!\n\n**Step 2:** Please enter your Email address:")
    
    elif isinstance(state, dict) and state.get("state") == "ASK_EMAIL":
        if not re.match(r"[^@]+@[^@]+\.[^@]+", m.text):
            return await m.reply_text("❌ Invalid Email! Please try again:")
        state["email"] = m.text
        state["state"] = "ASK_BITHDAY"
        await m.reply_text("Got it!\n\n**Step 3:** What is your Birthday? (DD/MM/YYYY)")

    elif isinstance(state, dict) and state.get("state") == "ASK_BITHDAY":
        state["birthday"] = m.text
        # Save to DB
        await users_col.update_one({"_id": uid}, {"$set": {
            "name": state["name"],
            "email": state["email"],
            "birthday": state["birthday"],
            "points": 0,
            "is_premium": False
        }}, upsert=True)
        del USER_STATES[uid]
        await m.reply_text("🎉 **Registration Complete!**\nYou can now use /start to access Flixora AI features.")
        await c.send_message(LOG_CHANNEL, f"🆕 **New User Registered**\nName: {state['name']}\nEmail: {state['email']}\nID: `{uid}`")

    # Help Request Logic
    elif state == "ASK_HELP_MSG":
        await c.send_message(LOG_CHANNEL, f"🆘 **Support Request**\nUser: {m.from_user.mention}\nID: `{uid}`\n\nMessage: {m.text}")
        del USER_STATES[uid]
        await m.reply_text("✅ Your request has been sent to our moderators in the Log Channel. They will contact you soon!")

    # AI Chat Logic
    else:
        # Check access (Verification logic)
        user = await users_col.find_one({"_id": uid})
        if not user or not user.get("email"): return
        
        last_v = user.get("last_verified", 0)
        if not user.get("is_premium") and (time.time() - last_v > 86400):
            link = await get_verify_link(uid)
            return await m.reply_text("🛑 Access Expired! Verify to continue.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔐 Verify", url=link)]]))

        # AI Response
        sticker = await m.reply_sticker(THINK_STICKER)
        # (Insert your OpenRouter call here)
        await asyncio.sleep(2)
        await sticker.delete()
        await m.reply_text("🤖 **AI:** Hello! I'm thinking about your message...")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb(c, q):
    if q.data == "ask_help":
        USER_STATES[q.from_user.id] = "ASK_HELP_MSG"
        await q.message.edit_text("💬 **Please type your query or problem.**\nYour message will be sent directly to our support team.")

# --- STARTUP ---
async def main():
    await web_server() # Opens the port for Render
    await app.start()
    print("Flixora AI Ecosystem is Active!")
    await idle()

if __name__ == "__main__":
    app.run(main())
