import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # API endpoints
    LIS_SKINS_API = "https://lis-skins.ru/market/730/"
    CS_MARKET_API = "https://cs.money/1.0/market/sell-orders"
    
    # Бот настройки
    MAX_RESULTS = 10  # Максимальное количество результатов
    CACHE_TIME = 300  # Кэширование на 5 минут