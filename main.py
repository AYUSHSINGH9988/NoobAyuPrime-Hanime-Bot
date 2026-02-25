import os
import json
import subprocess
import requests
import re
import uuid
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# 🌐 DUMMY WEB SERVER (RENDER KE LIYE)
# ==========================================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🤖 Universal Extractor Bot is Running Successfully on Render via Docker!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# 🤖 BOT CONFIGURATION & CODE
# ==========================================
API_ID = 33675350
API_HASH = "2f97c845b067a750c9f36fec497acf97"
BOT_TOKEN = "8798570619:AAE0Bz4umU7JMDn61AcssHwntSRyjNjzu-Q"

app = Client("universal_extractor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

SUPPORTED_SITES = ["hanime.tv", "hstream.moe", "oppai.stream", "hentaihaven.com", "ohentai.org", "hentaimama.io"]
PENDING_RESULTS = {}

def get_video_info(url):
    try:
        command = f'yt-dlp -j "{url}"'
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        data = json.loads(result.decode('utf-8'))
        title = data.get('title', 'Extracted_Video')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
        thumbnail = data.get('thumbnail', '')
        m3u8_link = data.get('url', '')
        return safe_title, thumbnail, m3u8_link
    except Exception as e:
        return None, None, str(e)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s[0])]

@app.on_message(filters.command("start"))
async def start(client, message):
    sites_list = "\n".join([f"✅ `{site}`" for site in SUPPORTED_SITES])
    welcome_text = (
        "✨ **Welcome to the Universal Extractor Bot!** ✨\n\n"
        f"🌐 **Supported Sites:**\n{sites_list}\n\n"
        "**Commands:**\n"
        "👉 Send any link directly for a **Single Video**.\n"
        "👉 Use `/batch <link>` for **Playlist/Series** extraction.\n"
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.command("batch"))
async def handle_batch(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Oops! URL missing.**\nFormat: `/batch <link>`")
        return
    
    url = message.command[1]
    if not any(site in url for site in SUPPORTED_SITES):
        return

    status = await message.reply_text("⏳ **Extracting Playlist using Plugins... Please wait!** 🕵️‍♂️")
    count = 0
    episodes_list = []

    try:
        command = f'yt-dlp -j --yes-playlist "{url}"'
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        lines = result.decode('utf-8').strip().split('\n')
        
        for line in lines:
            try:
                if not line.strip(): continue
                data = json.loads(line)
                title = data.get('title', 'Extracted_Video')
                safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
                m3u8_link = data.get('url', '')
                
                if m3u8_link and m3u8_link.startswith("http"):
                    count += 1
                    episodes_list.append((safe_title, m3u8_link))
            except Exception:
                continue
        
        if count > 0:
            episodes_list.sort(key=natural_sort_key) 
            req_id = str(uuid.uuid4())[:8]
            PENDING_RESULTS[req_id] = {"type": "batch", "episodes": episodes_list}
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Direct Links", callback_data=f"dir_{req_id}")],
                [InlineKeyboardButton("📥 Uploader Format (|)", callback_data=f"upl_{req_id}")]
            ])
            await status.edit_text(f"✅ **Extracted {count} Episodes!**\n\nKaunsa format chahiye?", reply_markup=buttons)
        else:
            await status.edit_text("❌ **No multiple episodes found.**")
            
    except Exception as e:
        await status.edit_text(f"❌ **Error during batch extraction:**\n`{str(e)}`")

@app.on_message(filters.text & ~filters.command(["start", "batch"]))
async def handle_message(client, message: Message):
    url = message.text
    if not any(site in url for site in SUPPORTED_SITES): return

    status = await message.reply_text("⏳ **Extracting video data...** 🕵️‍♂️")
    title, thumbnail, m3u8_link = get_video_info(url)
    
    if m3u8_link and m3u8_link.startswith("http"):
        req_id = str(uuid.uuid4())[:8]
        PENDING_RESULTS[req_id] = {"type": "single", "title": title, "m3u8": m3u8_link, "thumb": thumbnail}
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Direct Link", callback_data=f"dir_{req_id}")],
            [InlineKeyboardButton("📥 Uploader Format (|)", callback_data=f"upl_{req_id}")]
        ])
        await status.edit_text(f"🎬 **Title:** `{title}`\n\nKaunsa format chahiye?", reply_markup=buttons)
    else:
        await status.edit_text(f"❌ **Extraction Failed.**\n`{m3u8_link}`")

@app.on_callback_query()
async def callback_handler(client, query):
    action, req_id = query.data.split("_")
    
    if req_id not in PENDING_RESULTS:
        await query.answer("❌ Error! Ye link expire ho chuki hai. Wapas link bhejo!", show_alert=True)
        return
        
    await query.message.edit_text("⏳ **Generating your format...**")
    data = PENDING_RESULTS[req_id]
    
    if data["type"] == "single":
        title, m3u8, thumb = data["title"], data["m3u8"], data["thumb"]
        text = f"🎬 **Title:** `{title}`\n\n🔗 **Direct Link:**\n`{m3u8}`" if action == "dir" else f"🎬 **Title:** `{title}`\n\n📥 **Uploader Format:**\n`{m3u8} | {title}.mp4`"
            
        if thumb:
            await query.message.reply_photo(photo=thumb, caption=text)
            await query.message.delete()
        else:
            await query.message.edit_text(text)
            
    elif data["type"] == "batch":
        episodes = data["episodes"]
        count = len(episodes)
        final_text = f"🎬 **Batch Complete - {'Direct Links' if action == 'dir' else 'Uploader Format'} ({count} Episodes)**\n\n"
        
        for ep_title, ep_m3u8 in episodes:
            final_text += f"🎬 {ep_title}\n`{ep_m3u8}`\n\n" if action == "dir" else f"🎬 {ep_title}\n`{ep_m3u8} | {ep_title}.mp4`\n\n"
                
        if len(final_text) > 4000:
            file_name = "Batch_Links.txt"
            with open(file_name, "w", encoding="utf-8") as f: f.write(final_text.replace("`", "")) 
            await query.message.reply_document(document=file_name, caption=f"✅ **Extracted {count} episodes!**\nList lamba tha isliye text file bana di. 📁")
            os.remove(file_name)
            await query.message.delete()
        else:
            await query.message.edit_text(final_text)
            
    del PENDING_RESULTS[req_id]

if __name__ == "__main__":
    Thread(target=run_web).start()
    print("🤖 Universal Extractor Bot is Alive...")
    app.run()
