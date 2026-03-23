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
START_IMG = os.environ.get("START_IMG", "https://envs.sh/34_.jpg")
S_URL = os.environ.get("SHORTENER_URL", "")
S_API = os.environ.get("SHORTENER_API", "")
PORT = int(os.environ.get("PORT", "10000"))

THINK_STICKER = "CAACAgIAAxkBAAMIacD-Ra4_z1RuU2JTyYBeqq-qHrUAAvUAA_cCyA9HRphh0VDIsR4E"

# --- DB & APP ---
db = AsyncIOMotorClient(MONGO_URL)["FlixoraGPT"]
users_col = db["users"]
app = Client("FlixoraGPT", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# States
USER_STATES = {}

# --- MODELS PARSER ---
AVAIL_MODELS = []
for m in os.environ.get("MODELS_LIST", "").split(","):
    p = m.split("|")
    if len(p) == 3: AVAIL_MODELS.append({"name": p[0], "id": p[1], "desc": p[2]})

# --- WEB SERVER ---
async def web_server():
    server = web.Application()
    server.add_routes([web.get('/', lambda r: web.Response(text="Flixora Live"))])
    runner = web.AppRunner(server); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

# --- HELPERS ---
async def get_verify_link(uid):
    base = f"https://t.me/{app.me.username}?start=verify_{uid}"
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"https://{S_URL}/api?api={S_API}&url={base}")
            return r.json().get("shortenedUrl", base)
        except: return base

async def check_access(uid):
    u = await users_col.find_one({"_id": uid})
    if not u or u.get("is_premium"): return True
    return (time.time() - u.get("last_verified", 0)) < 86400

# --- AI LOGIC ---
async def ask_ai(prompt, uid):
    u = await users_col.find_one({"_id": uid})
    model = u.get("model", "openai/gpt-4o-mini")
    async with httpx.AsyncClient() as c:
        try:
            res = await c.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OR_KEY}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=60
            )
            return res.json()['choices'][0]['message']['content']
        except: return "❌ AI Error or Token Limit reached."

# --- COMMANDS ---
@app.on_message(filters.command("start") & filters.private)
async def start(c, m):
    uid = m.from_user.id
    user = await users_col.find_one({"_id": uid})

    if len(m.command) > 1 and m.command[1].startswith("verify_"):
        await users_col.update_one({"_id": uid}, {"$set": {"last_verified": time.time()}})
        return await m.reply_text("✅ 24h Access Granted!")

    if not user or not user.get("email"):
        USER_STATES[uid] = "ASK_NAME"
        return await m.reply_photo(START_IMG, caption="👋 **Welcome! Register to start.**\n\nEnter your **Full Name**:")

    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Models", callback_data="model_menu"), InlineKeyboardButton("👤 Account", callback_data="status")],
        [InlineKeyboardButton("🆘 Get Help", callback_data="ask_help"), InlineKeyboardButton("🔗 Refer", callback_data="refer")],
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{c.me.username}?startgroup=true")]
    ])
    await m.reply_photo(START_IMG, caption=f"✨ **Hello {user['name']}!**\nHow can Flixora assist you?", reply_markup=btns)

@app.on_message(filters.text & filters.private)
async def handle_msgs(c, m):
    uid = m.from_user.id
    state = USER_STATES.get(uid)

    if state == "ASK_NAME":
        USER_STATES[uid] = {"name": m.text, "st": "ASK_EMAIL"}
        await m.reply_text("📧 Now enter your **Email Address**:")
    elif isinstance(state, dict) and state.get("st") == "ASK_EMAIL":
        USER_STATES[uid]["email"] = m.text; USER_STATES[uid]["st"] = "ASK_BDAY"
        await m.reply_text("🎂 Enter your **Birthday** (DD/MM/YYYY):")
    elif isinstance(state, dict) and state.get("st") == "ASK_BDAY":
        await users_col.update_one({"_id": uid}, {"$set": {"name": state["name"], "email": state["email"], "birthday": m.text, "last_verified": 0}}, upsert=True)
        del USER_STATES[uid]
        await m.reply_text("🎉 Registered! Use /start")
        await c.send_message(LOG_CHANNEL, f"👤 **New User:** {state['name']}\nEmail: {state['email']}")
    
    elif state == "HELP_MSG":
        await c.send_message(LOG_CHANNEL, f"🆘 **Help Req from {uid}:**\n{m.text}")
        del USER_STATES[uid]
        await m.reply_text("✅ Sent to support channel!")

    else: # AI CHAT
        if not await check_access(uid):
            link = await get_verify_link(uid)
            return await m.reply_text("🛑 Access Expired! Verify:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔐 Verify", url=link)]]))
        
        # SHOW THINKING STICKER
        sticker = await m.reply_sticker(THINK_STICKER)
        ans = await ask_ai(m.text, uid)
        await sticker.delete()
        await m.reply_text(f"🤖 **Flixora:**\n\n{ans}")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb(c, q):
    uid = q.from_user.id
    if q.data == "model_menu":
        btns = [[InlineKeyboardButton(m['name'], callback_data=f"inf_{m['id']}")] for m in AVAIL_MODELS]
        await q.message.edit_caption("🧠 **Select AI Brain:**", reply_markup=InlineKeyboardMarkup(btns))
    elif q.data.startswith("inf_"):
        mid = q.data.split("_", 1)[1]
        m_info = next(i for i in AVAIL_MODELS if i['id'] == mid)
        await q.message.edit_caption(f"📝 **{m_info['name']}**\n{m_info['desc']}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Select", callback_data=f"set_{mid}")]]))
    elif q.data.startswith("set_"):
        mid = q.data.split("_", 1)[1]
        await users_col.update_one({"_id": uid}, {"$set": {"model": mid}})
        await q.answer("Model Selected!", show_alert=True)
    elif q.data == "status":
        u = await users_col.find_one({"_id": uid})
        await q.message.edit_caption(f"👤 **Account Info**\n\nName: `{u['name']}`\nEmail: `{u['email']}`\nBday: `{u['birthday']}`\nModel: `{u.get('model','Default')}`")
    elif q.data == "ask_help":
        USER_STATES[uid] = "HELP_MSG"
        await q.answer("Send your message now!", show_alert=True)

# --- START ---
async def main():
    await web_server()
    await app.start()
    await app.set_bot_commands([BotCommand("start", "Home"), BotCommand("status", "My Account")])
    await app.send_message(LOG_CHANNEL, "🚀 **Flixora AI Ecosystem Restarted**")
    print("Flixora Online!")
    await idle()

if __name__ == "__main__":
    app.run(main())
