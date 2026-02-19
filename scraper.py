import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp

# 1. Scraper Setup
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

def search_hentaihaven(query):
    """Search logic for HentaiHaven"""
    try:
        url = f"https://hentaihaven.xxx/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Checking HentaiHaven: {url}")
        
        resp = scraper.get(url)
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Result dhoondne ka logic
        res = soup.find('h2', class_='entry-title')
        if not res: res = soup.find('div', class_='post-content') # Backup
        
        if res and res.find('a'):
            return res.find('a')['href'], f"[HH] {res.text.strip()}"
            
    except Exception as e:
        print(f"HH Error: {e}")
    return None

def search_hanimered(query):
    """Search logic for Hanime.red"""
    try:
        url = f"https://hanime.red/?s={query.replace(' ', '+')}"
        print(f"DEBUG: Checking HanimeRed: {url}")
        
        resp = scraper.get(url)
        if resp.status_code != 200: return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Hanime.red structure (usually article or post-title)
        res = soup.find('h3', class_='title')
        if not res: res = soup.find('article') # Backup
        
        if res and res.find('a'):
            return res.find('a')['href'], f"[HR] {res.text.strip()}"

    except Exception as e:
        print(f"HR Error: {e}")
    return None

def search_anime(query):
    """Master search function jo dono sites check karega"""
    
    # 1. Pehle HentaiHaven check karo
    link, title = search_hentaihaven(query) or (None, None)
    if link: return link, title

    # 2. Agar nahi mila, to HanimeRed check karo
    link, title = search_hanimered(query) or (None, None)
    if link: return link, title
    
    return None, "❌ Koi result nahi mila dono sites par."

def get_stream_link(url):
    """Link extractor (Same as before)"""
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        return None, f"Error: {e}"
