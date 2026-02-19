import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp
import time

# Cloudscraper ko configure karte hain taaki wo delay lekar request kare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def search_anime(query):
    # 1. HentaiHaven Try
    try:
        url = f"https://hentaihaven.xxx/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Searching HH: {url}")
        
        # Thoda delay taaki bot na lage
        time.sleep(1) 
        resp = scraper.get(url)
        
        # Agar Cloudflare Challenge aaye (403 or 503)
        if resp.status_code in [403, 503]:
            print("⚠️ Cloudflare Challenge Detected on HH")
        elif resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            res = soup.find('h2', class_='entry-title')
            if not res: res = soup.find('div', class_='post-content')
            if res and res.find('a'):
                return res.find('a')['href'], f"[HH] {res.text.strip()}"
    except Exception as e:
        print(f"HH Error: {e}")

    # 2. HanimeRed Try (Backup)
    try:
        url = f"https://hanime.red/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Searching HR: {url}")
        
        time.sleep(1)
        resp = scraper.get(url)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            res = soup.find('h3', class_='title')
            if not res: res = soup.find('article')
            if res and res.find('a'):
                return res.find('a')['href'], f"[HR] {res.text.strip()}"
    except Exception as e:
        print(f"HR Error: {e}")

    return None, "❌ Cloudflare ne block kar diya ya result nahi mila."

def get_stream_link(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # Headers add karna zaroori hai
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': url
        }
    }
    
    print(f"DEBUG: Extracting from {url}")
    
    # Method 1: Direct Extraction
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        print(f"⚠️ Direct method failed: {e}")

    # Method 2: Iframe Scanning (Manual)
    try:
        resp = scraper.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        iframes = soup.find_all('iframe')
        
        for frame in iframes:
            src = frame.get('src')
            if src:
                if src.startswith("//"): src = "https:" + src
                print(f"🔎 Found Player: {src}")
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(src, download=False)
                        return info.get('url'), info.get('title')
                except:
                    continue
    except Exception as e:
        print(f"Deep Extraction Error: {e}")

    return None, "Extraction Failed (Cloudflare/DRM Protected)"
