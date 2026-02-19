import os

class Config:
    API_ID = int(os.environ.get("API_ID", "YOUR_API_ID_HERE"))
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH_HERE")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
  
