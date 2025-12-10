from fake_useragent import UserAgent

def get_random_user_agent():
    """Генерация случайного User-Agent"""
    try:
        ua = UserAgent()
        return ua.random
    except:
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def format_results(skins: list, market_filter: str = None):
    """
    Форматирование результатов для вывода в боте
    """
    if not skins:
        return "🚫 Скины не найдены"
    
    # Фильтрация по маркету если указан
    if market_filter:
        if market_filter.lower() == 'lis skins':
            market_filter = 'Lis Skins'
        elif market_filter.lower() == 'cs.money':
            market_filter = 'CS.Money'
        skins = [s for s in skins if s['market'] == market_filter]
    
    if not skins:
        return f"🚫 Не найдено скинов на {market_filter}"
    
    # Сортировка по цене
    skins = sorted(skins, key=lambda x: x['price'])
    
    messages = []
    messages.append(f"🔍 **Найдено {len(skins)} скинов:**\n")
    
    for i, skin in enumerate(skins[:10], 1):
        # Форматируем цену
        if skin['price'] >= 1000:
            price_str = f"{skin['price']:,.0f}".replace(',', ' ')
        else:
            price_str = f"{skin['price']:.2f}"
        
        message = (
            f"{i}. **{skin['name'][:50]}**\n"
            f"💰 *Цена:* {price_str} {skin['currency']}\n"
            f"🏪 *Маркет:* {skin['market']}\n"
        )
        
        # Добавляем дополнительную информацию если есть
        if skin.get('float'):
            message += f"🎯 *Float:* {skin['float']}\n"
        
        if skin.get('pattern'):
            message += f"🎨 *Pattern:* {skin['pattern']}\n"
        
        if skin.get('link'):
            # Сокращаем длинные ссылки
            short_link = skin['link'][:50] + "..." if len(skin['link']) > 50 else skin['link']
            message += f"🔗 [Купить]({skin['link']})\n"
        
        messages.append(message + "---")
    
    return "\n".join(messages)

def validate_price_input(price_str: str):
    """Валидация ввода цены"""
    try:
        if not price_str:
            return None
        price = float(price_str.replace(',', '.'))
        return price if price > 0 else None
    except:
        return None