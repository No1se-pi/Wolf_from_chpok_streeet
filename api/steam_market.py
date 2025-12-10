import requests
import json
from utils.helpers import get_random_user_agent

class SteamMarketAPI:
    @staticmethod
    def search_skins(skin_name: str, max_price: float = None, min_price: float = None):
        """
        Поиск скинов через Steam Community Market API
        Работает официально, без блокировок
        """
        try:
            url = "https://steamcommunity.com/market/search/render/"
            
            params = {
                'query': skin_name,
                'start': 0,
                'count': 20,  # Максимальное количество
                'search_descriptions': 0,
                'sort_column': 'price',
                'sort_dir': 'asc',
                'appid': 730,  # CS:GO/CS2
                'norender': 1,
                'currency': 5  # RUB - российские рубли
            }
            
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'application/json',
                'Referer': 'https://steamcommunity.com/market/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Steam API status: {response.status_code}")
                return []
            
            data = response.json()
            
            if not data.get('success', False):
                print(f"Steam API error: {data}")
                return []
            
            results = []
            
            for item in data.get('results', []):
                try:
                    # Цена в копейках, делим на 100 для рублей
                    price_rub = item.get('sell_price', 0) / 100
                    
                    # Фильтрация по цене
                    if max_price and price_rub > max_price:
                        continue
                    if min_price and price_rub < min_price:
                        continue
                    
                    # Получаем название
                    name = item.get('hash_name', 'Unknown')
                    
                    # Создаем ссылку
                    encoded_name = requests.utils.quote(name)
                    link = f"https://steamcommunity.com/market/listings/730/{encoded_name}"
                    
                    # Получаем изображение
                    image_url = None
                    if item.get('asset_description', {}).get('icon_url'):
                        icon_url = item['asset_description']['icon_url']
                        if icon_url.startswith('http'):
                            image_url = icon_url
                        else:
                            image_url = f"https://steamcommunity-a.akamaihd.net/economy/image/{icon_url}"
                    
                    results.append({
                        'name': name,
                        'price': price_rub,
                        'currency': 'RUB',
                        'link': link,
                        'image': image_url,
                        'market': 'Steam Market',
                        'sell_listings': item.get('sell_listings', 0)
                    })
                    
                except Exception as e:
                    print(f"Error parsing Steam item: {e}")
                    continue
            
            return results[:10]  # Ограничиваем вывод
            
        except Exception as e:
            print(f"Error searching Steam Market: {e}")
            return []
    
    @staticmethod
    def get_item_price(item_name: str):
        """Получение текущей цены предмета"""
        try:
            encoded_name = requests.utils.quote(item_name)
            url = f"https://steamcommunity.com/market/priceoverview/"
            
            params = {
                'appid': 730,
                'currency': 5,
                'market_hash_name': item_name
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return {
                        'lowest_price': data.get('lowest_price', '0'),
                        'median_price': data.get('median_price', '0'),
                        'volume': data.get('volume', '0')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting item price: {e}")
            return None