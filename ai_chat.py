from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
import requests
import asyncio
import info
from database import db_client
from utils.helpers import verify_access, check_rate_limit
from cachetools import TTLCache

# Response Cache: Stores responses for identical queries for 1 hour to reduce API costs.
ai_cache = TTLCache(maxsize=1000, ttl=3600)

async def call_openrouter_api(messages, model):
    """Calls the OpenRouter API asynchronously."""
    headers = {
        "Authorization": f"Bearer {info.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/YourBot", # Recommended by OpenRouter
        "X-Title": "FLIXORA AI"               # Recommended by OpenRouter
    }
    data = {"model": model, "messages": messages}
    
    loop = asyncio.get_event_loop()
    # Retry logic: Try up to 3 times
    for attempt in range(3):
        try:
            response = await loop.run_in_executor(None, lambda: requests.post(
                "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30
            ))
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(error_msg)
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt+1}: {e}")
            await asyncio.sleep(1) # Wait before retrying
            
    return "❌ I'm sorry, I'm having trouble connecting to the AI server right now. Please try again later."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages, checks access, and calls the AI."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # 1. Access Control
    if not await verify_access(update, context):
        return
        
    # 2. Rate Limiting
    if not check_rate_limit(user_id):
        await update.message.reply_text("⚠️ You are sending messages too fast. Please slow down!")
        return

    # 3. Check Cache
    if text in ai_cache:
        await update.message.reply_text(ai_cache[text], parse_mode="Markdown")
        return

    # 4. Show Animated "Thinking" message
    status_msg = await update.message.reply_text("⏳ Thinking...")

    # 5. Get user's selected model and chat history
    user = db_client.get_user(user_id)
    model = user.get("selected_model", info.MODELS["model_1"])
    history = context.user_data.get('chat_history', [])
    history.append({"role": "user", "content": text})
    if len(history) > 10: # Keep only the last 10 messages
        history = history[-10:]
    
    system_prompt = [{"role": "system", "content": "You are FLIXORA AI, a helpful and witty JARVIS-style assistant."}]
    
    # 6. Call API and get response
    try:
        reply = await call_openrouter_api(system_prompt + history, model)
        history.append({"role": "assistant", "content": reply})
        context.user_data['chat_history'] = history
        
        ai_cache[text] = reply
        
        # 7. Send the response, splitting if necessary
        if len(reply) > 4096:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i:i+4096], parse_mode="Markdown")
            await status_msg.delete()
        else:
            await status_msg.edit_text(reply, parse_mode="Markdown")
            
    except Exception as e:
        await status_msg.edit_text("⚠️ An error occurred. Please try again.")
        print(f"AI Chat Error: {e}")

chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)