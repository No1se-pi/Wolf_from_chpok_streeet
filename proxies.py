import random

PROXY_LIST = [
    # Добавьте здесь прокси если нужно
    # 'http://user:pass@proxy:port',
]

def get_random_proxy():
    """Получение случайного прокси"""
    if PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None