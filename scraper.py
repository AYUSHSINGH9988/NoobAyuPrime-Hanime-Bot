import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp

# 1. Scraper Setup (Browser simulation)
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def search_hentaihaven(query):
    try:
        url = f"https://hentaihaven.xxx/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Searching HH: {url}")
        resp = scraper.get(url)
        if resp.status_code != 200: return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Structure check
        res = soup.find('h2', class_='entry-title')
        if not res: res = soup.find('div', class_='post-content')
        
        if res and res.find('a'):
            return res.find('a')['href'], f"[HH] {res.text.strip()}"
    except Exception as e:
        print(f"HH Search Error: {e}")
    return None

def search_hanimered(query):
    try:
        url = f"https://hanime.red/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Searching HR: {url}")
        resp = scraper.get(url)
        if resp.status_code != 200: return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        res = soup.find('h3', class_='title')
        if not res: res = soup.find('article')
        
        if res and res.find('a'):
            return res.find('a')['href'], f"[HR] {res.text.strip()}"
    except Exception as e:
        print(f"HR Search Error: {e}")
    return None

def search_anime(query):
    # Pehle HH check karega, fir HR
    link, title = search_hentaihaven(query) or (None, None)
    if link: return link, title

    link, title = search_hanimered(query) or (None, None)
    if link: return link, title
    
    return None, "❌ Koi result nahi mila."

def get_stream_link(url):
    """
    Advanced Extractor:
    1. Pehle direct try karta hai.
    2. Fail hone par page ke andar IFRAME/VIDEO tags dhundhta hai.
    """
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    }

    print(f"DEBUG: Processing Page: {url}")

    # METHOD 1: Direct yt-dlp try
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        print(f"⚠️ Direct method failed: {e}")

    # METHOD 2: Deep Extraction (Manual Iframe Hunt)
    try:
        print("🔄 Trying Deep Extraction (Iframe Hunt)...")
        response = scraper.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Sare iframes nikalo
        iframes = soup.find_all('iframe')
        
        for frame in iframes:
            src = frame.get('src')
            if src:
                if src.startswith("//"): src = "https:" + src
                print(f"🔎 Found Player: {src}")
                
                # Player link ko yt-dlp me try karo
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(src, download=False)
                        return info.get('url'), info.get('title')
                except:
                    continue # Agar ye player fail hua to agla try karo

    except Exception as e:
        print(f"❌ Deep extraction error: {e}")

    return None, "Error: Stream not found."
