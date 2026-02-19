from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from scraper import search_anime, get_stream_link

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
        await status_msg.edit_text("❌ Koi result nahi mila.")
        return

    await status_msg.edit_text(f"✅ **Found:** {title}\n🔗 Link nikaal raha hoon...")

    # 2. Extract Step
    stream_url, vid_title = get_stream_link(page_link)

    if stream_url:
        # User ko button bhejein
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch Online", url=stream_url)]
        ])
        
        await status_msg.edit_text(
            f"🎬 **{vid_title}**\n\nLink Generate ho gaya hai!",
            reply_markup=buttons
        )
        # Optional: Raw link bhi bhej dein copy karne ke liye
        await message.reply_text(f"**Link:**\n`{stream_url}`")
    else:
        await status_msg.edit_text("❌ Video link fetch nahi ho paya (shayad premium/DRM content ho).")

if __name__ == "__main__":
    print("Bot Started...")
    app.run()
      
