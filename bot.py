import os, asyncio, time, datetime, httpx
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
PORT = os.environ.get("PORT", "8080")

# Thinking Sticker ID
THINK_STICKER = "CAACAgIAAxkBAAMIacD-Ra4_z1RuU2JTyYBeqq-qHrUAAvUAA_cCyA9HRphh0VDIsR4E"

# --- PARSE MODELS FROM ENV ---
AVAILABLE_MODELS = []
raw_models = os.environ.get("MODELS_LIST", "").split(",")
for m in raw_models:
    parts = m.split("|")
    if len(parts) == 3:
        AVAILABLE_MODELS.append({"name": parts[0], "id": parts[1], "desc": parts[2]})

# --- DB SETUP ---
db = AsyncIOMotorClient(MONGO_URL)["FlixoraGPT"]
users_col = db["users"]

app = Client("FlixoraGPT", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- WEB SERVER ---
async def handle(r): return web.Response(text="Flixora AI is Live")
async def web_server():
    server = web.Application(); server.add_routes([web.get('/', handle)])
    runner = web.AppRunner(server); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(PORT)).start()

# --- HELPERS ---
async def get_verify_link(user_id):
    base = f"https://t.me/{app.me.username}?start=verify_{user_id}_{int(time.time())}"
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://{S_URL}/api?api={S_API}&url={base}")
        return res.json().get("shortenedUrl", base)

async def check_access(user_id):
    u = await users_col.find_one({"_id": user_id})
    if not u: return False
    if u.get("is_premium"): return True
    return (time.time() - u.get("last_verified", 0)) < 86400

async def ask_ai(prompt, user_id):
    u = await users_col.find_one({"_id": user_id})
    model = u.get("model", AVAILABLE_MODELS[0]['id'] if AVAILABLE_MODELS else "openai/gpt-4o-mini")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OR_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=60
            )
            return res.json()['choices'][0]['message']['content']
        except: return "❌ AI Busy. Try again later."

# --- COMMANDS ---
@app.on_message(filters.command("start"))
async def start(c, m):
    uid = m.from_user.id
    if len(m.command) > 1:
        if m.command[1].startswith("verify_"):
            await users_col.update_one({"_id": uid}, {"$set": {"last_verified": time.time()}}, upsert=True)
            return await m.reply_text("✅ **24h Access Unlocked!** You can now chat with Flixora AI.")
        if m.command[1].startswith("ref_"):
            ref_id = int(m.command[1].split("_")[1])
            if ref_id != uid:
                await users_col.update_one({"_id": ref_id}, {"$inc": {"points": 10}}, upsert=True)
                try: await c.send_message(ref_id, "🎁 +10 Points! Someone joined via your link.")
                except: pass

    await users_col.update_one({"_id": uid}, {"$set": {"name": m.from_user.first_name}}, upsert=True)
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Select Model", callback_data="model_menu"), InlineKeyboardButton("👤 Account", callback_data="status")],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer"), InlineKeyboardButton("💎 Premium", callback_data="prem")],
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{c.me.username}?startgroup=true")]
    ])
    await m.reply_text(f"✨ **Welcome to Flixora Master AI**\n\nI am your AI assistant. Choose a model below and start chatting!", reply_markup=btn)

@app.on_message(filters.text & filters.private & ~filters.command(["start", "refer", "mode"]))
async def chat(c, m):
    if not await check_access(m.from_user.id):
        link = await get_verify_link(m.from_user.id)
        return await m.reply_text("🚫 **Verification Required!**\nUnlock 24h chat access by completing one link:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔐 Unlock Now", url=link)]]))
    
    sticker = await m.reply_sticker(THINK_STICKER)
    reply = await ask_ai(m.text, m.from_user.id)
    await sticker.delete()
    await m.reply_text(f"🤖 **Flixora AI:**\n\n{reply}")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb(c, q):
    uid = q.from_user.id
    if q.data == "model_menu":
        btns = [[InlineKeyboardButton(m['name'], callback_data=f"info_{m['id']}")] for m in AVAILABLE_MODELS]
        btns.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
        await q.message.edit_text("🧠 **Choose an AI Brain:**", reply_markup=InlineKeyboardMarkup(btns))
    
    elif q.data.startswith("info_"):
        mid = q.data.split("_", 1)[1]
        m_info = next(i for i in AVAILABLE_MODELS if i['id'] == mid)
        text = f"📝 **Model:** {m_info['name']}\n\n**Description:** {m_info['desc']}\n\nDo you want to switch to this model?"
        btn = [[InlineKeyboardButton("✅ Confirm Selection", callback_data=f"set_{mid}")], [InlineKeyboardButton("⬅️ Back", callback_data="model_menu")]]
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btn))

    elif q.data.startswith("set_"):
        mid = q.data.split("_", 1)[1]
        await users_col.update_one({"_id": uid}, {"$set": {"model": mid}}, upsert=True)
        await q.answer("✅ Model Updated!", show_alert=True)
        await q.message.edit_text("✨ **Model set successfully!** You can now start chatting.")

    elif q.data == "status":
        u = await users_col.find_one({"_id": uid})
        await q.message.edit_text(f"👤 **Your Account**\n\nPoints: `{u.get('points',0)}` \nModel: `{u.get('model','Default')}`\nPremium: `{'Yes' if u.get('is_premium') else 'No'}`")

    elif q.data == "home":
        await start(c, q.message)

# --- STARTUP ---
async def main():
    await web_server(); await app.start()
    await app.set_bot_commands([BotCommand("start", "Home"), BotCommand("mode", "Select AI"), BotCommand("status", "Check Points")])
    await app.send_message(LOG_CHANNEL, "🚀 **Flixora Master GPT is Online**")
    await idle()

if __name__ == "__main__":
    app.run(main())