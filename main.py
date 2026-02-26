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
import uuid
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 🔥 THE MASTER FIX FOR PYTHON 3.14 (SABSE UPAR HONA CHAHIYE) 🔥
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# ==========================================
# 🌐 KOYEB / RENDER HEALTH CHECK FIX 
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is ALIVE and running with Quality Selector!")

def keep_alive():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

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
# 🤖 BOT & MONGODB CONFIGURATION 
# ==========================================
API_ID = 33675350
API_HASH = "2f97c845b067a750c9f36fec497acf97"
BOT_TOKEN = "8798570619:AAE0Bz4umU7JMDn61AcssHwntSRyjNjzu-Q"
DUMP_CHAT_ID = -1003831827071

app = Client("universal_extractor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
SUPPORTED_SITES = ["hanime.tv", "hstream.moe", "oppai.stream", "hentaihaven.com", "ohentai.org", "hentaimama.io"]

MONGO_URL = "mongodb+srv://salonisingh6265_db_user:U50ONNZZFUbh0iQI@cluster0.41mb27f.mongodb.net/?appName=Cluster0"
mongo_client = None
file_cache = None
PENDING_TASKS = {} # 👈 Memory for Quality Selector Tasks

def get_cache():
    global mongo_client, file_cache
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(MONGO_URL)
        db = mongo_client["UniversalBotDB"]
        file_cache = db["VideoCacheFiles"]
    return file_cache

# ==========================================
# 📊 PROGRESS BAR & METADATA HELPERS
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
            await message.edit_text(f"📤 **{action}...**\n\n{tmp}")
        except Exception:
            pass

def get_video_info(url):
    try:
        command = f'yt-dlp -j "{url}"'
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        data = json.loads(result.decode('utf-8'))
        title = data.get('title', 'Extracted_Video')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
        thumb = data.get('thumbnail', '')
        duration = data.get('duration', 0)
        return safe_title, data.get('url', ''), thumb, duration
    except Exception:
        return None, None, None, 0

async def extract_metadata(video_path):
    duration = 0
    thumb_path = f"{video_path}.jpg"

    try:
        dur_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_path}"'
        dur_proc = await asyncio.create_subprocess_shell(dur_cmd, stdout=asyncio.subprocess.PIPE)
        dur_out, _ = await dur_proc.communicate()
        duration = int(float(dur_out.decode('utf-8').strip()))
    except:
        pass

    try:
        thumb_cmd = f'ffmpeg -v error -y -i "{video_path}" -ss 00:00:02 -vframes 1 -vf scale=320:-1 "{thumb_path}"'
        thumb_proc = await asyncio.create_subprocess_shell(thumb_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await thumb_proc.communicate()
    except:
        pass

    if not os.path.exists(thumb_path):
        thumb_path = None

    return duration, thumb_path

# ==========================================
# 📥 DOWNLOAD & UPLOAD LOGIC
# ==========================================
async def process_video(client, original_message, vid_title, m3u8_url, yt_thumb, yt_duration, quality):
    status = await original_message.reply_text(f"🔍 **Checking Database for:** `{vid_title}` **({quality}p)**...")

    cache = get_cache()
    # 🌟 NEW: DB ab Quality bhi check karega!
    cached_video = await cache.find_one({"title": vid_title, "quality": str(quality)})
    
    if cached_video:
        await status.edit_text(f"⚡ **Video Found ({quality}p)! Sending Instantly...**")
        await client.send_video(
            chat_id=original_message.chat.id,
            video=cached_video["file_id"],
            caption=f"🎬 **{vid_title}** [{quality}p]"
        )
        await status.delete()
        return

    await status.edit_text(f"📥 **Downloading:** `{vid_title}`\n⚙️ **Quality:** `{quality}p`\n⏳ Initiating Download...")
    file_name = f"{vid_title}_{quality}p.mp4"

    # 🌟 NEW: yt-dlp ab user ki batayi hui Quality download karega (-S "res:quality")
    cmd = f'yt-dlp --newline -S "res:{quality}" -o "{file_name}" "{m3u8_url}"'
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    last_update_time = time.time()
    while True:
        line = await proc.stdout.readline()
        if not line: break

        line_text = line.decode('utf-8').strip()
        if "[download]" in line_text and "%" in line_text:
            current_time = time.time()
            if current_time - last_update_time > 5:
                clean_text = line_text.replace("[download]", "").strip()
                try:
                    await status.edit_text(f"📥 **Downloading:** `{vid_title}`\n⚙️ **Quality:** `{quality}p`\n\n📊 **Status:** `{clean_text}`")
                    last_update_time = current_time
                except Exception:
                    pass

    await proc.wait()

    if not os.path.exists(file_name):
        await status.edit_text(f"❌ **Download Failed for:** `{vid_title}`")
        return

    await status.edit_text("📤 **Extracting Metadata & Preparing to Upload...**")

    real_duration, real_thumb = await extract_metadata(file_name)
    final_duration = real_duration if real_duration > 0 else (int(yt_duration) if yt_duration else 0)

    if not real_thumb and yt_thumb:
        try:
            real_thumb = f"{file_name}.jpg"
            urllib.request.urlretrieve(yt_thumb, real_thumb)
        except:
            real_thumb = None

    start_time = time.time()

    try:
        dump_msg = await client.send_video(
            chat_id=DUMP_CHAT_ID,
            video=file_name,
            caption=f"🎬 **{vid_title}** [{quality}p]",
            thumb=real_thumb if (real_thumb and os.path.exists(real_thumb)) else None,
            duration=final_duration,
            supports_streaming=True,
            progress=progress_bar,
            progress_args=(status, start_time, "Uploading to Telegram")
        )

        if dump_msg and dump_msg.video:
            # 🌟 NEW: DB ab File ID ke sath Quality bhi Save Karega!
            await cache.insert_one({
                "title": vid_title,
                "quality": str(quality),
                "file_id": dump_msg.video.file_id
            })

        await client.send_video(
            chat_id=original_message.chat.id,
            video=dump_msg.video.file_id,
            caption=f"🎬 **{vid_title}** [{quality}p]"
        )
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ **Upload Error:**\n`{str(e)}`")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        if real_thumb and os.path.exists(real_thumb):
            os.remove(real_thumb)

# ==========================================
# 🎛️ INLINE KEYBOARD (QUALITY SELECTOR)
# ==========================================
def get_quality_keyboard(task_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 1080p", callback_data=f"q_1080_{task_id}"),
         InlineKeyboardButton("📺 720p", callback_data=f"q_720_{task_id}")],
        [InlineKeyboardButton("📱 480p", callback_data=f"q_480_{task_id}"),
         InlineKeyboardButton("📻 360p", callback_data=f"q_360_{task_id}")]
    ])

# ==========================================
# 🤖 BOT COMMANDS
# ==========================================
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
    if not any(site in url for site in SUPPORTED_SITES): return

    status = await message.reply_text("⏳ **Finding episodes from API...** 🕵️‍♂️")

    try:
        if "hanime.tv" in url:
            slug = url.split('/hentai/')[-1].split('?')[0]
            api_url = f"https://hanime.tv/api/v8/video?id={slug}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*'
            }

            r = requests.get(api_url, headers=headers)
            if r.status_code == 200:
                franchise_videos = r.json().get('hentai_franchise_hentai_videos', [{'slug': slug}])
                
                # 🌟 TASK SAVE KAREIN AUR QUALITY POOCHEIN
                task_id = str(uuid.uuid4())[:8]
                PENDING_TASKS[task_id] = {
                    "type": "batch", 
                    "episodes": franchise_videos,
                    "original_msg": message
                }
                
                await status.edit_text(
                    f"🔍 **Found {len(franchise_videos)} episodes!**\n\nKaunsi Quality me download karna hai? 👇",
                    reply_markup=get_quality_keyboard(task_id)
                )
            else:
                await status.edit_text("❌ **Failed to connect to API.**")
                return
        else:
            await status.edit_text("🔍 **Extracting Playlist...**")
            await status.edit_text("Batch for other sites is not fully implemented yet.")

    except Exception as e:
        await status.edit_text(f"❌ **Error:**\n`{str(e)}`")

@app.on_message(filters.text & ~filters.command(["start", "batch"]))
async def handle_message(client, message: Message):
    url = message.text
    if not any(site in url for site in SUPPORTED_SITES): return

    # 🌟 SINGLE LINK KE LIYE BHI PEHLE QUALITY POOCHEGA
    task_id = str(uuid.uuid4())[:8]
    PENDING_TASKS[task_id] = {
        "type": "single",
        "url": url,
        "original_msg": message
    }
    
    await message.reply_text(
        "🎬 **Link Detected!**\n\nKaunsi Quality me download karna hai? 👇",
        reply_markup=get_quality_keyboard(task_id)
    )

# ==========================================
# 🎛️ CALLBACK HANDLER FOR QUALITY SELECTION
# ==========================================
@app.on_callback_query(filters.regex(r"^q_(\d+)_(.+)$"))
async def quality_callback(client, query):
    quality = int(query.matches[0].group(1))
    task_id = query.matches[0].group(2)
    
    if task_id not in PENDING_TASKS:
        return await query.answer("❌ Error! Ye link expire ho chuki hai. Wapas link bhejo!", show_alert=True)
        
    task = PENDING_TASKS[task_id]
    original_msg = task["original_msg"]
    
    await query.message.edit_text(f"✅ **Quality Set to {quality}p! Starting Extraction...**")
    
    if task["type"] == "single":
        title, m3u8_link, thumb, duration = get_video_info(task["url"])
        if m3u8_link:
            await process_video(client, original_msg, title, m3u8_link, thumb, duration, quality)
        else:
            await query.message.edit_text("❌ **Extraction Failed.**")
            
    elif task["type"] == "batch":
        franchise_videos = task["episodes"]
        for index, vid in enumerate(franchise_videos):
            vid_slug = vid.get('slug')
            if not vid_slug: continue
            vid_url = f"https://hanime.tv/videos/hentai/{vid_slug}"
            
            title, m3u8_link, thumb, duration = get_video_info(vid_url)
            if m3u8_link:
                # Same original message pass kar rahe hain taaki har video ke liye alag message aaye
                await process_video(client, original_msg, title, m3u8_link, thumb, duration, quality)
                
                # Anti-ban sleep (sirf tab jab next episode bacha ho)
                if index < len(franchise_videos) - 1:
                    await asyncio.sleep(5)
            else:
                await original_msg.reply_text(f"❌ **Extraction Failed for:** `{vid_url}`")
                
        await original_msg.reply_text(f"🎉 **Batch Download Complete ({len(franchise_videos)} Episodes) in {quality}p!**")
        
    del PENDING_TASKS[task_id]

if __name__ == "__main__":
    print("🤖 Universal Auto-DL Bot is Alive with Quality Selector...")
    keep_alive() 
    app.run()
