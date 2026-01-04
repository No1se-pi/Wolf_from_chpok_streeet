import requests


API_KEY = "1Lu2nW8fh5J0ll929MORSRb64NjngKb"
BASE_URL = "https://market.csgo.com/api/v2"


# ---------- БАЗОВЫЕ ФУНКЦИИ ----------

def search_item_by_hash_name(hash_name: str, currency: str = "RUB") -> list[dict]:
    """
    Поиск предмета по market_hash_name.
    Возвращает список офферов (price, count и т.п.).
    """
    url = f"{BASE_URL}/search-item-by-hash-name"
    params = {
        "key": API_KEY,
        "v": 2,
        "hash_name": hash_name,
        "currency": currency,
    }
    resp = requests.get(url, params=params, timeout=10)
    print("SEARCH STATUS:", resp.status_code)
    print("SEARCH TEXT:", resp.text[:200])
    resp.raise_for_status()

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API error (search): {data}")
    return data.get("data") or []


def get_item_history(hash_name: str, currency: str = "RUB") -> dict | None:
    """
    История продаж конкретного предмета по hash_name.
    """
    url = f"{BASE_URL}/get-list-items-info"
    params = [
        ("key", API_KEY),
        ("v", 2),
        ("list_hash_name[]", hash_name),
        ("currency", currency),
    ]
    resp = requests.get(url, params=params, timeout=10)
    print("HISTORY STATUS:", resp.status_code)
    print("HISTORY TEXT:", resp.text[:200])
    resp.raise_for_status()

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API error (history): {data}")

    data_dict = data.get("data") or {}
    return data_dict.get(hash_name)


def get_bid_ask(hash_name: str, currency: str = "RUB") -> dict:
    """
    Стакан по предмету: заявки на покупку (bid) и продажу (ask).
    """
    url = f"{BASE_URL}/bid-ask"
    params = {
        "key": API_KEY,
        "v": 2,
        "hash_name": hash_name,
        "currency": currency,
    }
    resp = requests.get(url, params=params, timeout=10)
    print("BOOK STATUS:", resp.status_code)
    print("BOOK TEXT:", resp.text[:200])
    resp.raise_for_status()
    return resp.json()


# ---------- ФОРМАТИРУЮЩИЕ ФУНКЦИИ ----------

def format_best_offer(hash_name: str) -> str:
    offers = search_item_by_hash_name(hash_name)

    if not offers:
        return "Предложений по этому предмету нет."

    # сортируем по цене и берём самый дешёвый оффер
    best = sorted(offers, key=lambda o: o.get("price", 10**18))[0]

    name = best.get("market_hash_name")
    price = best.get("price")
    count = best.get("count")

    text = (
        f"Название: {name}\n"
        f"Лучшая цена: {price}\n"
        f"Лотов по этой цене: {count}"
    )
    return text


def format_item_history(hash_name: str) -> str:
    info = get_item_history(hash_name)
    if not info:
        return "История по этому предмету не найдена."

    avg_price = info.get("average")
    min_price = info.get("min")
    max_price = info.get("max")
    history = info.get("history") or []

    last_ts, last_price = history[0] if history else (None, None)

    text = (
        f"История продаж: {hash_name}\n"
        f"Средняя цена: {avg_price}\n"
        f"Мин. цена: {min_price}\n"
        f"Макс. цена: {max_price}\n"
        f"Последняя сделка (цена): {last_price}"
    )
    return text


def format_bid_ask(hash_name: str) -> str:
    data = get_bid_ask(hash_name)

    bids = data.get("bid") or []
    asks = data.get("ask") or []

    best_bid = bids[0] if bids else None
    best_ask = asks[0] if asks else None

    lines = [f"Стакан по: {hash_name}"]

    if best_bid:
        lines.append(
            f"Лучшая покупка: {best_bid['price']} ({best_bid['total']} шт.)"
        )
    else:
        lines.append("Лучшая покупка: нет заявок")

    if best_ask:
        lines.append(
            f"Лучшая продажа: {best_ask['price']} ({best_ask['total']} шт.)"
        )
    else:
        lines.append("Лучшая продажа: нет офферов")

    return "\n".join(lines)


# ---------- ТЕСТОВЫЙ ЗАПУСК ----------

def main():
    name = "AK-47 | Case Hardened (Field-Tested)"

    print("--- Лучший оффер ---")
    print(format_best_offer(name))
    print()

    print("--- История ---")
    print(format_item_history(name))
    print()

    print("--- Стакан ---")
    print(format_bid_ask(name))
    print()


if __name__ == "__main__":
    main()
