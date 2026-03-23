import info

async def send_log(context, text):
    try:
        if info.LOG_CHANNEL:
            await context.bot.send_message(chat_id=info.LOG_CHANNEL, text=f"🔔 **FLIXORA LOG**\n\n{text}", parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to send log: {e}")