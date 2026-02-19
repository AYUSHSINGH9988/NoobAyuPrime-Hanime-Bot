import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp
import time
import re

# Cloudscraper setup
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

# --- HELPER FUNCTIONS ---

def is_ad_domain(url):
    """Check karega ki ye link Ad hai ya asli video"""
    ad_domains = ["havenclick", "afr.php", "doubleclick", "googlesyndication", "chaturbate"]
    for domain in ad_domains:
        if domain in url:
            return True
    return False

def extract_video(url):
    """
    Ek URL se video nikaalne ki koshish karega.
    Agar fail hua to None return karega.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # Browser Impersonation (Anti-Bot Bypass)
        'extractor_args': {'generic': ['impersonate']},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': url
        }
    }

    print(f"DEBUG: Extracting from {url}")

    # 1. Direct Try
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        print(f"⚠️ Direct extraction failed: {e}")

    # 2. Iframe / Embed Hunt (Deep Scan)
    try:
        resp = scraper.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Sare iframes dhundho
        iframes = soup.find_all('iframe')
        
        for frame in iframes:
            src = frame.get('src')
            if not src: continue
            
            # Protocol fix
            if src.startswith("//"): src = "https:" + src
            
            # AD FILTER (Yahan ads skip honge)
            if is_ad_domain(src):
                print(f"🗑️ Skipping Ad: {src}")
                continue
                
            print(f"🔎 Found Potential Player: {src}")
            
            # Is player ko try karo
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(src, download=False)
                    return info.get('url'), info.get('title')
            except:
                continue # Next iframe try karo

    except Exception as e:
        print(f"❌ Deep extraction error: {e}")
    
    return None, None

# --- SEARCH LOGIC ---

def search_and_get_link(query):
    """
    Ye function Search aur Extract dono ek saath karega.
    Pehle HH try karega -> Agar video mili to return.
    Nahi to HR try karega -> Agar video mili to return.
    """
    
    # === SITE 1: HENTAIHAVEN ===
    try:
        print(f"🔍 Searching HentaiHaven for: {query}")
        url = f"https://hentaihaven.xxx/?s={query.replace(' ', '+')}"
        resp = scraper.get(url)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            res = soup.find('h2', class_='entry-title')
            if not res: res = soup.find('div', class_='post-content')
            
            if res and res.find('a'):
                page_link = res.find('a')['href']
                title = res.text.strip()
                print(f"✅ HH Page Found: {title}")
                
                # Abhi ke abhi extract karo
                stream_url, vid_title = extract_video(page_link)
                if stream_url:
                    return stream_url, f"[HH] {vid_title}"
                else:
                    print("⚠️ HH par link mila par video extract nahi hui. Switching...")
    except Exception as e:
        print(f"HH Search Error: {e}")

    # === SITE 2: HANIME.RED (Backup) ===
    try:
        print(f"🔍 Switching to Hanime.red for: {query}")
        url = f"https://hanime.red/?s={query.replace(' ', '+')}"
        resp = scraper.get(url)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            res = soup.find('h3', class_='title')
            if not res: res = soup.find('article')
            
            if res and res.find('a'):
                page_link = res.find('a')['href']
                title = res.text.strip()
                print(f"✅ HR Page Found: {title}")
                
                # Extract karo
                stream_url, vid_title = extract_video(page_link)
                if stream_url:
                    return stream_url, f"[HR] {vid_title}"
    except Exception as e:
        print(f"HR Search Error: {e}")

    return None, "❌ Koi playable video nahi mila (Try checking exact spelling)."

# Compatibility for main.py
# (main.py calls search_anime and get_stream_link separately, 
# but now we do it in one go. So we create wrappers)

def search_anime(query):
    # Hum directly result return karenge taaki main.py confuse na ho
    # Lekin main.py expect karta hai (page_link, title).
    # Hum 'page_link' ki jagah seedha 'stream_url' bhej denge hack karke.
    link, title = search_and_get_link(query)
    return link, title

def get_stream_link(url):
    # Kyunki humne upar hi link nikaal liya, 
    # ye function bas wahi link wapas kar dega.
    # Ye hack hai taaki main.py change na karna pade.
    return url, "Video Ready"
