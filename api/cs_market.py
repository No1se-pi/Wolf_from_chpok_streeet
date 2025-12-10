import requests
import json
import time
import re
from utils.helpers import get_random_user_agent

class CSMarketAPI:
    @staticmethod
    def search_skins(skin_name: str, max_price: float = None, min_price: float = None):
        """
        Поиск скинов на cs.money через альтернативные методы
        """
        try:
            # Используем основной сайт с поиском через параметры
            url = "https://cs.money/csgo/trade/"
            
            params = {
                'search': skin_name,
                'sort': 'price',
                'order': 'asc'
            }
            
            headers = {
                'User-Agent': get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Referer': 'https://cs.money/'
            }
            
            # Добавляем задержку
            time.sleep(1)
            
            session = requests.Session()
            response = session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"CS Money status: {response.status_code}")
                return CSMarketAPI._search_fallback(skin_name, max_price)
            
            # Ищем данные в JavaScript коде
            html = response.text
            
            # Пробуем найти JSON данные
            import re
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'"items"\s*:\s*\[(.*?)\]',
                r'\{\s*"data"\s*:\s*\[(.*?)\]\s*\}'
            ]
            
            results = []
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for match in matches:
                    try:
                        if pattern.startswith('window'):
                            data = json.loads(match)
                            items = data.get('items', []) if 'items' in data else []
                        else:
                            # Пробуем дополнить до валидного JSON
                            json_str = f'{{"items": [{match}]}}'
                            data = json.loads(json_str)
                            items = data.get('items', [])
                        
                        for item in items[:10]:
                            try:
                                item_data = CSMarketAPI._parse_api_item(item)
                                if item_data:
                                    if max_price and item_data['price'] > max_price:
                                        continue
                                    if min_price and item_data['price'] < min_price:
                                        continue
                                    results.append(item_data)
                            except:
                                continue
                        
                        if results:
                            return results[:10]
                            
                    except json.JSONDecodeError:
                        continue
            
            # Если не нашли JSON, пробуем парсить HTML
            return CSMarketAPI._parse_html(html, skin_name, max_price)
            
        except Exception as e:
            print(f"Error searching CS.Money: {e}")
            return []

    @staticmethod
    def _parse_api_item(item):
        """Парсинг элемента из API"""
        try:
            name = item.get('title') or item.get('name') or item.get('market_hash_name', 'Unknown')
            price = item.get('price')
            
            if not price:
                # Пробуем получить цену из разных полей
                price = item.get('price', {}).get('RUB') or item.get('price_rub') or item.get('cost')
            
            if not price:
                return None
            
            # Конвертируем в число
            try:
                price = float(price)
            except:
                return None
            
            item_id = item.get('id') or item.get('item_id', '')
            link = f"https://cs.money/csgo/trade/?search={name.replace(' ', '+')}"
            
            # Получаем float и pattern
            float_value = item.get('float') or item.get('float_value')
            pattern = item.get('pattern') or item.get('paintseed')
            
            return {
                'name': name[:100],
                'price': price,
                'currency': 'RUB',
                'link': link,
                'image': item.get('icon_url') or item.get('image'),
                'market': 'CS.Money',
                'float': float_value,
                'pattern': pattern
            }
            
        except Exception as e:
            return None

    @staticmethod
    def _parse_html(html, skin_name, max_price):
        """Парсинг HTML страницы"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html5lib')
            results = []
            
            # Пробуем найти элементы скинов
            item_selectors = [
                '.item',
                '.skin-item',
                '.product',
                '.card',
                '[class*="item"]',
                '[class*="skin"]'
            ]
            
            for selector in item_selectors:
                items = soup.select(selector)
                if len(items) > 3:
                    for item in items[:10]:
                        try:
                            text = item.get_text(strip=True, separator=' ')
                            
                            # Ищем цену
                            price_match = re.search(r'(\d+[\s,.]?\d*)\s*(₽|руб|RUB)', text)
                            if not price_match:
                                continue
                            
                            price_str = price_match.group(1).replace(' ', '').replace(',', '.')
                            price = float(price_str)
                            
                            if max_price and price > max_price:
                                continue
                            
                            # Извлекаем название
                            name_match = re.search(r'([A-Za-z0-9\- ]+?)(?=\s*\d)', text)
                            if name_match:
                                name = name_match.group(1).strip()
                            else:
                                # Берем первые слова до цены
                                name_parts = text.split(str(int(price)))
                                name = name_parts[0].strip() if name_parts else skin_name
                            
                            # Ищем ссылку
                            link_elem = item.find('a', href=True)
                            link = link_elem['href'] if link_elem else f"https://cs.money/csgo/trade/?search={skin_name.replace(' ', '+')}"
                            
                            if not link.startswith('http'):
                                link = f"https://cs.money{link}"
                            
                            results.append({
                                'name': name[:80],
                                'price': price,
                                'currency': 'RUB',
                                'link': link,
                                'market': 'CS.Money'
                            })
                            
                        except Exception as e:
                            continue
                    
                    if results:
                        return results[:10]
            
            return results
            
        except Exception as e:
            print(f"HTML parsing error: {e}")
            return []

    @staticmethod
    def _search_fallback(skin_name: str, max_price: float = None):
        """
        Запасной метод поиска через другие источники
        """
        # Можно добавить поиск через Steam Community Market или другие API
        return []