import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
from config import Config
from scraper import search_anime, get_stream_link

# --- WEB SERVER SETUP (Koyeb Health Check) ---
async def health_check_server():
    async def handle_root(request):
        return web.Response(text="Bot is Running Successfully!", status=200)

    app_web = web.Application()
    app_web.add_routes([web.get('/', handle_root)])
    
    # Koyeb aur Render $PORT environment variable use karte hain (Default: 8080)
    port = int(os.environ.get("PORT", 8080))
    
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Web Server started on Port {port}")

# --- BOT SETUP ---
app = Client(
    "AnimeBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Hello! Anime ka naam bhejo, main link dhundh kar dunga.\n\n"
        "Example: `Naruto` or `/watch Naruto`"
    )

@app.on_message(filters.text & ~filters.command("start"))
async def handle_search(client, message):
    query = message.text
    status_msg = await message.reply_text(f"🔎 **Searching:** `{query}`...")

    # 1. Search Step
    page_link, title = search_anime(query)

    if not page_link:
        await status_msg.edit_text(f"{title}") # Error message show karega
        return

    await status_msg.edit_text(f"✅ **Found:** {title}\n🔗 Extracting Video Link...")

    # 2. Extract Step
    stream_url, vid_title = get_stream_link(page_link)

    if stream_url:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch Online", url=stream_url)]
        ])
        
        await status_msg.edit_text(
            f"🎬 **{vid_title}**\n\nLink Generated!",
            reply_markup=buttons
        )
        await message.reply_text(f"`{stream_url}`")
    else:
        await status_msg.edit_text("❌ Video link fetch nahi ho paya (Cloudflare/DRM issue).")

# --- MAIN EXECUTION ---
async def main():
    # Pehle Web Server start karein
    await health_check_server()
    
    # Phir Bot start karein
    print("🤖 Bot Starting...")
    await app.start()
    print("🚀 Bot Started Successfully!")
    
    # Bot ko idle rakhein taaki wo band na ho
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Asyncio loop chalao
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
