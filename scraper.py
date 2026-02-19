import cloudscraper
from bs4 import BeautifulSoup
import yt_dlp

# Cloudflare scraper setup
scraper = cloudscraper.create_scraper()

def search_anime(query):
    """
    Search function: Query leta hai aur result URL return karta hai.
    Note: Website ke HTML structure ke hisab se 'find' logic change karna pad sakta hai.
    """
    try:
        # Example URL structure (Isse apni target site se replace karein)
        # Agar site hai: https://site.com/?s=naruto
        base_url = "https://hentaihaven.xxx" 
        search_url = f"{base_url}/?s={query.replace(' ', '+')}"
        
        response = scraper.get(search_url)
        if response.status_code != 200:
            return None, "Website unreachable"

        soup = BeautifulSoup(response.text, 'html.parser')

        # Logic to find the first result
        # Site ke HTML me check karein ki result kis class me hai.
        # Usually it is inside <h2 class="entry-title"><a href="...">
        result = soup.find('h2', class_='entry-title')
        
        if not result:
            # Backup check
            result = soup.find('h3', class_='entry-title')

        if result and result.find('a'):
            link = result.find('a')['href']
            title = result.text.strip()
            return link, title
        
        return None, "No results found."

    except Exception as e:
        return None, f"Error: {e}"

def get_stream_link(url):
    """
    Page URL se direct video link nikaalta hai yt-dlp use karke.
    """
    options = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title')
    except Exception as e:
        return None, f"Extraction Failed: {e}"
      
