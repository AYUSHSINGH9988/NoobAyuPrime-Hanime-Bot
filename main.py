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

# 🔥 THE MASTER FIX FOR PYTHON 3.14 🔥
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
        self.wfile.write(b"Bot is ALIVE with Task Cancellation!")

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

MONGO_URL = "mongodb+srv://salonisingh6265_db_user:U50ONNZZFUbh0iQI@cluster0.41mb27f.mongodb.net/?appName=Cluster0"
mongo_client = None
file_cache = None

# 🌟 TASK MANAGERS 🌟
PENDING_TASKS = {} 
ACTIVE_TASKS = {} # Ye cancel status ko track karega

def get_cache():
    global mongo_client, file_cache
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(MONGO_URL)
        db = mongo_client["UniversalBotDB"]
        file_cache = db["VideoCacheFiles"]
    return file_cache

# ==========================================
# 📊 NEW PREMIUM PROGRESS BAR UI 
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

async def progress_bar(current, total, message, start_time, action, task_id):
    # 🌟 UPLOAD CANCELLATION CHECK 🌟
    if ACTIVE_TASKS.get(task_id, {}).get("cancel"):
        raise Exception("CANCELLED")

    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0

        filled = math.floor(percentage / 10)
        empty = 10 - filled
        progress = "▰" * filled + "▱" * empty

        tmp = (
            f"╭━━━━━━━━━━━━━━━╮\n"
            f"┣ {progress} **{round(percentage, 2)}%**\n"
            f"╰━━━━━━━━━━━━━━━╯\n"
            f"📈 **Size:** `{humanbytes(current)} / {humanbytes(total)}`\n"
            f"⚡ **Speed:** `{humanbytes(speed)}/s`\n"
            f"⏳ **ETA:** `{time_formatter(time_to_completion)}`"
        )
        
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Task", callback_data=f"cancel_{task_id}")]])
        try:
            await message.edit_text(f"🚀 **{action}...**\n\n{tmp}", reply_markup=cancel_btn)
        except Exception:
            pass

# ==========================================
# 🌟 DUAL EXTRACTOR LOGIC
# ==========================================
def get_video_info(url, is_generic=False):
    try:
        command = f'yt-dlp -j "{url}"'
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        data = json.loads(result.decode('utf-8'))
        
        title = data.get('title', 'Extracted_Video')
        safe_title = "".join([c for c in title if c.isalnum() or c==' ']).strip()
        thumb = data.get('thumbnail', '')
        duration = data.get('duration', 0)
        vid_url = data.get('url', url)
        
        qualities = [1080, 720, 480, 360] 
        
        if is_generic:
            try:
                available_qualities = set()
                for f in data.get('formats', []):
                    height = f.get('height')
                    vcodec = f.get('vcodec')
                    if height and isinstance(height, int) and vcodec != 'none':
                        available_qualities.add(height)
                if available_qualities:
                    qualities = sorted(list(available_qualities), reverse=True)
            except:
                pass
                
        return safe_title, vid_url, thumb, duration, qualities
    except Exception as e:
        return None, None, None, 0, []

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
async def process_video(client, original_message, vid_title, video_url, yt_thumb, yt_duration, quality, task_id):
    # 🌟 BATCH CANCELLATION CHECK 🌟
    if ACTIVE_TASKS.get(task_id, {}).get("cancel"):
        return False

    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Task", callback_data=f"cancel_{task_id}")]])
    status = await original_message.reply_text(f"🔍 **Checking Database for:** `{vid_title[:30]}...` **({quality}p)**", reply_markup=cancel_btn)

    cache = get_cache()
    cached_video = await cache.find_one({"title": vid_title, "quality": str(quality)})
    
    if cached_video:
        await status.edit_text(f"⚡ **Video Found ({quality}p)! Sending Instantly...**")
        await client.send_video(
            chat_id=original_message.chat.id,
            video=cached_video["file_id"],
            caption=f"🎬 **{vid_title}** [{quality}p]"
        )
        await status.delete()
        return True

    await status.edit_text(f"📥 **Downloading:** `{vid_title[:30]}...`\n⚙️ **Quality:** `{quality}p`\n⏳ Initiating...", reply_markup=cancel_btn)
    file_name = f"{vid_title}_{quality}p.mp4"

    cmd = f'yt-dlp --newline -S "res:{quality}" -o "{file_name}" "{video_url}"'
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    # 🌟 ATTACH PROCESS FOR CANCELLATION 🌟
    if task_id in ACTIVE_TASKS:
        ACTIVE_TASKS[task_id]["proc"] = proc

    last_update_time = time.time()
    while True:
        # 🌟 DOWNLOAD CANCELLATION CHECK 🌟
        if ACTIVE_TASKS.get(task_id, {}).get("cancel"):
            try: proc.terminate() 
            except: pass
            break

        line = await proc.stdout.readline()
        if not line: break

        line_text = line.decode('utf-8').strip()
        if "[download]" in line_text and "%" in line_text:
            current_time = time.time()
            if current_time - last_update_time > 5:
                clean_text = line_text.replace("[download]", "").strip()
                try:
                    await status.edit_text(f"📥 **Downloading:** `{vid_title[:30]}...`\n⚙️ **Quality:** `{quality}p`\n\n🚀 **Status:** `{clean_text}`", reply_markup=cancel_btn)
                    last_update_time = current_time
                except Exception:
                    pass

    await proc.wait()

    if ACTIVE_TASKS.get(task_id, {}).get("cancel"):
        if os.path.exists(file_name): os.remove(file_name)
        await status.edit_text("❌ **Task Cancelled by User.**")
        return False

    if not os.path.exists(file_name):
        await status.edit_text(f"❌ **Download Failed.**\nShayad ye quality available nahi hai, doosri try karein.")
        return False

    await status.edit_text("📤 **Extracting Metadata & Preparing to Upload...**", reply_markup=cancel_btn)

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
            progress_args=(status, start_time, "Uploading to Telegram", task_id)
        )

        if dump_msg and dump_msg.video:
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
        return True
    except Exception as e:
        if str(e) == "CANCELLED":
            await status.edit_text("❌ **Upload Cancelled by User.**")
        else:
            await status.edit_text(f"❌ **Upload Error:**\n`{str(e)}`")
        return False
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        if real_thumb and os.path.exists(real_thumb):
            os.remove(real_thumb)

# ==========================================
# 🎛️ DYNAMIC KEYBOARD GENERATOR
# ==========================================
def get_quality_keyboard(task_id, qualities):
    buttons = []
    row = []
    for q in qualities[:8]: 
        row.append(InlineKeyboardButton(f"🎥 {q}p", callback_data=f"q_{q}_{task_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

SUPPORTED_SITES = ["hanime.tv", "hstream.moe", "oppai.stream", "hentaihaven.com", "ohentai.org", "hentaimama.io"]

# ==========================================
# 🤖 BOT COMMANDS
# ==========================================
@app.on_message(filters.command("start"))
async def start(client, message):
    welcome_text = (
        "✨ **Welcome to the Universal Extractor Bot!** ✨\n\n"
        "🌐 **Features:**\n"
        "✅ Support for Hanime Series & Plugin \n"
        "✅ `/batch` Support for ALL Playlist Sites\n"
        "✅ `/ytdlleech` for Generic Sites (YouTube, Twitter, etc.)\n"
        "✅ Dynamic Quality Selector & Task Cancellation\n\n"
        "**Commands:**\n"
        "👉 Paste `Hanime link` directly.\n"
        "👉 Use `/batch <playlist-link>` for any Series.\n"
        "👉 Use `/ytdlleech <link>` for any other site.\n"
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.text & ~filters.command(["start", "batch", "ytdlleech"]))
async def handle_message(client, message: Message):
    url = message.text
    if not any(site in url for site in SUPPORTED_SITES): 
        return 

    status = await message.reply_text("⏳ **Scanning Link...** 🕵️‍♂️")
    title, vid_url, thumb, duration, qualities = get_video_info(url, is_generic=False)

    if title:
        task_id = str(uuid.uuid4())[:8]
        PENDING_TASKS[task_id] = {
            "type": "single",
            "url": url, 
            "title": title,
            "thumb": thumb,
            "duration": duration,
            "original_msg": message
        }
        await status.edit_text(
            f"🎬 **{title[:50]}...**\n\n✅ Link Supported! Kaunsi Quality chahiye? 👇",
            reply_markup=get_quality_keyboard(task_id, qualities)
        )
    else:
        await status.edit_text("❌ **Extraction Failed. Please verify the link.**")

@app.on_message(filters.command("ytdlleech"))
async def handle_ytdlleech(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ **Oops! URL missing.**\nFormat: `/ytdlleech <link>`")
        
    url = message.command[1]
    status = await message.reply_text("⏳ **Scanning Generic Link & Fetching Qualities...** 🕵️‍♂️")
    
    title, vid_url, thumb, duration, qualities = get_video_info(url, is_generic=True)

    if title:
        task_id = str(uuid.uuid4())[:8]
        PENDING_TASKS[task_id] = {
            "type": "single",
            "url": vid_url, 
            "title": title,
            "thumb": thumb,
            "duration": duration,
            "original_msg": message
        }
        await status.edit_text(
            f"🎬 **{title[:50]}...**\n\n✅ Found Available Qualities! Select one: 👇",
            reply_markup=get_quality_keyboard(task_id, qualities)
        )
    else:
        await status.edit_text("❌ **Extraction Failed. yt-dlp could not process this link.**")

@app.on_message(filters.command("batch"))
async def handle_batch(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ **Oops! URL missing.**\nFormat: `/batch <link>`")
        return

    url = message.command[1]
    status = await message.reply_text("⏳ **Finding episodes from Playlist/Series...** 🕵️‍♂️")

    try:
        if "hanime.tv" in url:
            slug = url.split('/hentai/')[-1].split('?')[0]
            api_url = f"https://hanime.tv/api/v8/video?id={slug}"
            r = requests.get(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                franchise_videos = r.json().get('hentai_franchise_hentai_videos', [{'slug': slug}])
                task_id = str(uuid.uuid4())[:8]
                PENDING_TASKS[task_id] = {
                    "type": "batch", 
                    "site": "hanime",
                    "episodes": franchise_videos,
                    "original_msg": message
                }
                await status.edit_text(
                    f"🔍 **Found {len(franchise_videos)} episodes!**\n\nKaunsi Quality me saare episodes download karne hain? 👇",
                    reply_markup=get_quality_keyboard(task_id, [1080, 720, 480, 360])
                )
            else:
                await status.edit_text("❌ **Failed to connect to Hanime API.**")
        else:
            await status.edit_text("⏳ **Scanning Playlist structure via yt-dlp...** (Thoda time lag sakta hai) 🕵️‍♂️")
            cmd = f'yt-dlp -j --flat-playlist "{url}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await proc.communicate()
            lines = stdout.decode('utf-8').strip().split('\n')
            
            generic_episodes = []
            for line in lines:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    ep_url = data.get('url') or data.get('webpage_url')
                    if ep_url:
                        generic_episodes.append({'url': ep_url, 'title': data.get('title', 'Episode')})
                except: pass
            
            if generic_episodes:
                first_vid_url = generic_episodes[0]['url']
                _, _, _, _, qualities = get_video_info(first_vid_url, is_generic=True)
                task_id = str(uuid.uuid4())[:8]
                PENDING_TASKS[task_id] = {
                    "type": "batch", 
                    "site": "generic",
                    "episodes": generic_episodes,
                    "original_msg": message
                }
                await status.edit_text(
                    f"🔍 **Found {len(generic_episodes)} episodes in this Playlist!**\n\nChoose Quality 👇",
                    reply_markup=get_quality_keyboard(task_id, qualities)
                )
            else:
                await status.edit_text("❌ **No episodes found.**\nShayad is site par yt-dlp playlist read nahi kar pa raha.")

    except Exception as e:
        await status.edit_text(f"❌ **Error:**\n`{str(e)}`")

# ==========================================
# 🎛️ CALLBACK HANDLER FOR QUALITY SELECTION & CANCEL
# ==========================================
@app.on_callback_query(filters.regex(r"^q_(\d+)_(.+)$"))
async def quality_callback(client, query):
    quality = int(query.matches[0].group(1))
    task_id = query.matches[0].group(2)
    
    if task_id not in PENDING_TASKS:
        return await query.answer("❌ Error! Ye task expire ho chuka hai. Wapas link bhejo!", show_alert=True)
        
    task = PENDING_TASKS.pop(task_id) # Move from pending to active
    original_msg = task["original_msg"]
    
    # 🌟 REGISTER ACTIVE TASK FOR CANCELLATION 🌟
    ACTIVE_TASKS[task_id] = {"cancel": False, "proc": None}
    
    await query.message.edit_text(f"✅ **Quality Set to {quality}p! Starting Download...**")
    
    if task["type"] == "single":
        await process_video(client, original_msg, task["title"], task["url"], task["thumb"], task["duration"], quality, task_id)
            
    elif task["type"] == "batch":
        franchise_videos = task["episodes"]
        for index, vid in enumerate(franchise_videos):
            if ACTIVE_TASKS.get(task_id, {}).get("cancel"):
                await original_msg.reply_text("❌ **Batch Process stopped by user.**")
                break
                
            if task.get("site") == "hanime":
                vid_slug = vid.get('slug')
                if not vid_slug: continue
                vid_url = f"https://hanime.tv/videos/hentai/{vid_slug}"
                is_generic_site = False
            else:
                vid_url = vid.get('url')
                is_generic_site = True
            
            title, _, thumb, duration, _ = get_video_info(vid_url, is_generic=is_generic_site)
            if title:
                success = await process_video(client, original_msg, title, vid_url, thumb, duration, quality, task_id)
                if not success and ACTIVE_TASKS.get(task_id, {}).get("cancel"): break
                if index < len(franchise_videos) - 1:
                    await asyncio.sleep(5) 
            else:
                await original_msg.reply_text(f"❌ **Failed for:** `{vid_url}`")
                
        if not ACTIVE_TASKS.get(task_id, {}).get("cancel"):
            await original_msg.reply_text(f"🎉 **Batch Download Complete in {quality}p!**")
            
    # Cleanup task
    if task_id in ACTIVE_TASKS:
        del ACTIVE_TASKS[task_id]

# 🌟 CANCEL BUTTON HANDLER 🌟
@app.on_callback_query(filters.regex(r"^cancel_(.+)$"))
async def cancel_callback(client, query):
    task_id = query.matches[0].group(1)
    if task_id in ACTIVE_TASKS:
        ACTIVE_TASKS[task_id]["cancel"] = True
        proc = ACTIVE_TASKS[task_id].get("proc")
        if proc:
            try: proc.terminate()
            except: pass
        await query.answer("⛔ Stopping task...", show_alert=True)
    else:
        await query.answer("⚠️ Task already finished or not found.", show_alert=True)

if __name__ == "__main__":
    print("🤖 Universal Auto-DL Bot is Alive with Task Cancellation...")
    keep_alive() 
    app.run()