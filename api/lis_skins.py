import requests
from bs4 import BeautifulSoup
import re
import json
import time
from utils.helpers import get_random_user_agent

class LisSkinsAPI:
    @staticmethod
    def search_skins(skin_name: str, max_price: float = None, min_price: float = None):
        """
        Поиск скинов на lis-skins.ru
        """
        try:
            # Используем .com вместо .ru
            url = f"https://lis-skins.com/market/730/"
            
            params = {
                'search': skin_name,
                'sort': 'price',
                'order': 'asc'
            }
            
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'DNT': '1'
            }
            
            # Добавляем задержку между запросами
            time.sleep(1)
            
            session = requests.Session()
            response = session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Lis Skins status: {response.status_code}")
                # Попробуем альтернативный метод
                return LisSkinsAPI.search_skins_api(skin_name, max_price)
            
            # Используем html5lib вместо lxml
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Пробуем разные селекторы
            results = []
            
            # Попробуем найти элементы с классами
            item_selectors = [
                '.market-item',
                '.item',
                '.product',
                '.col-md-3',
                '.col-lg-3',
                '[class*="item"]',
                '[class*="product"]'
            ]
            
            for selector in item_selectors:
                items = soup.select(selector)
                if len(items) > 3:  # Нашли достаточно элементов
                    for item in items[:15]:
                        try:
                            item_data = LisSkinsAPI._parse_item(item)
                            if item_data:
                                # Фильтрация по цене
                                if max_price and item_data['price'] > max_price:
                                    continue
                                if min_price and item_data['price'] < min_price:
                                    continue
                                results.append(item_data)
                        except Exception as e:
                            continue
                    break
            
            return results[:10]
            
        except Exception as e:
            print(f"Error searching Lis Skins: {e}")
            return []

    @staticmethod
    def _parse_item(item):
        """Парсинг одного элемента"""
        try:
            # Получаем текст элемента
            text = item.get_text(strip=True, separator=' ')
            if len(text) < 10:
                return None
            
            # Ищем цену
            price_match = re.search(r'(\d+[\s,.]?\d*[\s,.]?\d*)\s*(₽|руб|RUB|RUB|р\.|рублей)', text, re.I)
            if not price_match:
                return None
            
            price_str = price_match.group(1).replace(' ', '').replace(',', '.')
            try:
                price = float(price_str)
            except:
                return None
            
            # Извлекаем название (убираем цену из текста)
            name_text = re.sub(r'\d+[\s,.]?\d*[\s,.]?\d*\s*(₽|руб|RUB|RUB|р\.|рублей)', '', text, flags=re.I)
            name_parts = name_text.strip().split()
            if len(name_parts) < 2:
                return None
            
            # Берем первые 3-5 слов как название
            name = ' '.join(name_parts[:min(5, len(name_parts))])
            
            # Ищем ссылку
            link = None
            link_elem = item.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    link = f"https://lis-skins.com{href}"
                elif href.startswith('http'):
                    link = href
            
            # Ищем изображение
            image_url = None
            img_elem = item.find('img', src=True)
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src:
                    if src.startswith('/'):
                        image_url = f"https://lis-skins.com{src}"
                    elif src.startswith('http'):
                        image_url = src
            
            return {
                'name': name[:100],
                'price': price,
                'currency': 'RUB',
                'link': link,
                'image': image_url,
                'market': 'Lis Skins',
                'source': 'web'
            }
            
        except Exception as e:
            return None

    @staticmethod
    def search_skins_api(skin_name: str, max_price: float = None):
        """
        Альтернативный метод поиска
        """
        # Можно добавить поиск через другие API или методы
        return []