import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp
import re

# Cloudscraper Setup (Chrome Browser ban kar jayega)
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def get_player_from_page(url):
    """
    Page khol kar hidden Iframe (Video Player) dhundhta hai.
    """
    try:
        print(f"🕵️ Bypassing Cloudflare on: {url}")
        # Timeout zaroori hai taaki agar site slow ho to bot atke nahi
        response = scraper.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"⚠️ Page Access Failed: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- PLAYER HUNTING LOGIC ---
        iframes = soup.find_all('iframe')
        
        for frame in iframes:
            src = frame.get('src')
            if not src: continue
            
            # Ad Blockers (Ye domains skip honge)
            if any(x in src for x in ['havenclick', 'ads', 'banner', 'chaturbate', 'doubleclick']):
                continue
                
            # URL fix
            if src.startswith("//"): src = "https:" + src
            
            print(f"🎯 Player Found: {src}")
            return src 
            
        print("❌ Koi video player (iframe) nahi mila.")
        return None

    except Exception as e:
        print(f"Error parsing page: {e}")
        return None

def extract_video_data(player_url):
    """
    Player URL se direct video link nikalta hai.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'generic': ['impersonate']},
    }
    
    try:
        print(f"⬇️ Extracting video from player: {player_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(player_url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        print(f"❌ yt-dlp extraction failed: {e}")
        return None, None

def search_anime(query):
    # ==============================
    # PRIORITY 1: HANIME.RED
    # ==============================
    try:
        search_url = f"https://hanime.red/?s={query.replace(' ', '+')}"
        print(f"🔎 [Priority 1] Searching Hanime.red: {search_url}")
        
        resp = scraper.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Hanime.red structure
        res = soup.find('h3', class_='title')
        if not res: res = soup.find('article')
        
        if res and res.find('a'):
            page_link = res.find('a')['href']
            title = res.text.strip()
            print(f"✅ Page Found on HR: {title}")
            
            # Extract Player
            player_url = get_player_from_page(page_link)
            if player_url:
                # Extract Video
                stream, vid_title = extract_video_data(player_url)
                if stream:
                    return stream, f"[HR] {vid_title or title}"
                else:
                    # Agar stream nahi mili, player link return kar do
                    return player_url, f"[HR] {title} (Web Player)"
    except Exception as e:
        print(f"HR Error: {e}")

    # ==============================
    # PRIORITY 2: HENTAIHAVEN (Backup)
    # ==============================
    try:
        search_url = f"https://hentaihaven.xxx/?s={query.replace(' ', '+')}"
        print(f"🔎 [Priority 2] Switching to HentaiHaven: {search_url}")
        
        resp = scraper.get(search_url, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # HH structure
        res = soup.find('h2', class_='entry-title')
        if not res: res = soup.find('div', class_='post-content')
        
        if res and res.find('a'):
            page_link = res.find('a')['href']
            title = res.text.strip()
            print(f"✅ Page Found on HH: {title}")
            
            player_url = get_player_from_page(page_link)
            if player_url:
                stream, vid_title = extract_video_data(player_url)
                if stream:
                    return stream, f"[HH] {vid_title or title}"
                else:
                    return player_url, f"[HH] {title} (Web Player)"
            
    except Exception as e:
        print(f"HH Error: {e}")

    return None, "❌ Koi video nahi mili (Dono sites check kar li)."

# Wrapper for main.py compatibility
def get_stream_link(url):
    return url, "Video Ready"
