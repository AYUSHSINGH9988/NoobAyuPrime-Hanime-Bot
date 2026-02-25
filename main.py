import os
import json
import subprocess
import requests
import re
import urllib.request
import zipfile
import stat
import asyncio
import time
import math
from pyrogram import Client, filters
from pyrogram.types import Message

# ==========================================
# ⚙️ PURE PYTHON DENO AUTO-INSTALLER 
# ==========================================
print("⚙️ Checking system requirements...")
try:
    deno_dir = os.path.expanduser("~/.deno/bin")
    deno_path = os.path.join(deno_dir, "deno")
    
    if not os.path.exists(deno_path):
        os.makedirs(deno_dir, exist_ok=True)
        url = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"
        zip_file = os.path.join(deno_dir, "deno.zip")
        urllib.request.urlretrieve(url, zip_file)
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(deno_dir)
        st = os.stat(deno_path)
        os.chmod(deno_path, st.st_mode | stat.S_IEXEC)
        os.remove(zip_file)
    
    if deno_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{deno_dir}:{os.environ.get('PATH', '')}"
except Exception as e:
    pass

# ==========================================
# 🤖 BOT CONFIGURATION 
# ==========================================
API_ID = 33675350
API_HASH = "2f97c845b067a750c9f36fec497acf97"
BOT_TOKEN = "8798570619:AAE0Bz4umU7JMDn61AcssHwntSRyjNjzu-Q"

# 👇 YAHAN APNE DUMP CHANNEL KA ID DAALIYE (-100 SE SHURU HOTA HAI) 👇
DUMP_CHAT_ID = -1003831827071

app = Client("universal_extractor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
SUPPORTED_SITES = ["hanime.tv", "hstream.moe", "oppai.stream", "hentaihaven.com", "ohentai.org", "hentaimama.io"]

# ==========================================
# 📊 PROGRESS BAR & HELPERS
# ==========================================
def humanbytes(size):
    if not size: return "0 B"
    power, n = 1024, 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def time_formatter(milliseconds):
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + ((str(hours) + "h, ") if hours else "") + ((str(minutes) + "m, ") if minutes else "") + ((str(seconds) + "s") if seconds else "")
    return tmp

async def progress_bar(current, total, message, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        
        progress = "[{0}{1}]".format(
            ''.join(["█" for _ in range(math.floor(percentage / 10))]),
            ''.join(["░" for _ in range(10 - math.floor(percentage / 10))])
        )
        
        tmp = (
            f"**Progress:** {round(percentage, 2)}%\n"
            f"{progress}\n"
            f"**Loaded:** {humanbytes(current)} / {humanbytes(total)}\n"
            f"**Speed:** {humanbytes(speed)}/s\n"
            f"**ETA:** {time_formatter(time_to_completion)}"
        )
        try:
            await message.edit_text(f"⏳ **{action}...**\n\n{tmp}")
        except Exception:
            pass

def get_video_info(url):
    try:
        command = f'yt-dlp -j "{url}"'
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        data = json.loads(result.decode('utf-8'))
        title = data.get('title', 'Extracted_Video')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
        return safe_title, data.get('url', '')
    except Exception:
        return None, None

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s[0])]

# ==========================================
# 📥 DOWNLOAD & UPLOAD LOGIC
# ==========================================
async def process_video(client, original_message, vid_title, m3u8_url):
    status = await original_message.reply_text(f"📥 **Downloading:** `{vid_title}`\n⏳ Please wait...")
    file_name = f"{vid_title}.mp4"
    
    # Download direct inside server
    cmd = f'yt-dlp -o "{file_name}" "{m3u8_url}"'
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
    
    if not os.path.exists(file_name):
        await status.edit_text(f"❌ **Download Failed for:** `{vid_title}`")
        return
        
    await status.edit_text("📤 **Preparing to Upload...**")
    start_time = time.time()
    
    try:
        # Upload to Dump Channel
        dump_msg = await client.send_video(
            chat_id=DUMP_CHAT_ID,
            video=file_name,
            caption=f"🎬 **{vid_title}**",
            progress=progress_bar,
            progress_args=(status, start_time, "Uploading to Telegram")
        )
        # Forward to User
        await dump_msg.copy(original_message.chat.id)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ **Upload Error:**\n`{str(e)}`")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# ==========================================
# 🤖 BOT COMMANDS
# ==========================================
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✨ **Universal Extractor Bot Alive!** ✨\n\nSend me a supported link or use `/batch <link>` for playlists. I will Auto-Download and Upload it for you!")

@app.on_message(filters.command("batch"))
async def handle_batch(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Oops! URL missing.**\nFormat: `/batch <link>`")
        return
    
    url = message.command[1]
    if not any(site in url for site in SUPPORTED_SITES): return

    status = await message.reply_text("⏳ **Finding all episodes...** 🕵️‍♂️")

    try:
        if "hanime.tv" in url:
            slug = url.split('/hentai/')[-1].split('?')[0]
            api_url = f"https://hanime.tv/api/v8/video?id={slug}"
            r = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                franchise_videos = r.json().get('hentai_franchise_hentai_videos', [{'slug': slug}])
                await status.edit_text(f"🔍 **Found {len(franchise_videos)} episodes! Extracting and Downloading back-to-back...**")
                
                for index, vid in enumerate(franchise_videos):
                    vid_slug = vid.get('slug')
                    if not vid_slug: continue
                    vid_url = f"https://hanime.tv/videos/hentai/{vid_slug}"
                    title, m3u8_link = get_video_info(vid_url)
                    
                    if m3u8_link:
                        # Direct Auto-Process each episode (No sleep/rest anymore)
                        await process_video(client, message, title, m3u8_link)
            else:
                await status.edit_text("❌ **Failed to connect to API.**")
                return
        else:
            await status.edit_text("🔍 **Extracting Playlist...**")
            # Logic for other sites batch can be added similarly
            await status.edit_text("Batch for other sites is processing... (Will add full logic if needed)")
            
    except Exception as e:
        await status.edit_text(f"❌ **Error:**\n`{str(e)}`")

@app.on_message(filters.text & ~filters.command(["start", "batch"]))
async def handle_message(client, message: Message):
    url = message.text
    if not any(site in url for site in SUPPORTED_SITES): return

    status = await message.reply_text("⏳ **Extracting M3U8 Link...** 🕵️‍♂️")
    title, m3u8_link = get_video_info(url)
    
    if m3u8_link and m3u8_link.startswith("http"):
        await status.delete()
        # Direct Auto-Process
        await process_video(client, message, title, m3u8_link)
    else:
        await status.edit_text("❌ **Extraction Failed.**")

if __name__ == "__main__":
    print("🤖 Universal Auto-DL Bot is Alive...")
    app.run()
