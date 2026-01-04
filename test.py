import time
import requests
from typing import Optional


API_KEY = "1Lu2nW8fh5J0ll929MORSRb64NjngKb"
BASE_URL = "https://market.csgo.com/api/v2"


session = requests.Session()
session.params = {
    "key": API_KEY,
    "v": 2,
}
session.headers.update({
    "Accept": "application/json",
})


# ---------- ЗАПРОС СКИНА С МАКСИМУМОМ ДАННЫХ ----------

def fetch_offers(hash_name: str, currency: str = "RUB") -> list[dict]:
    """
    Берёт все офферы по названию с доп.данными (float, наклейки, и т.п. если есть).
    """
    url = f"{BASE_URL}/search-item-by-hash-name-specific"
    params = {
        "hash_name": hash_name,
        "currency": currency,
        "with_stickers": 1,
        "lang": "en",
    }
    resp = session.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API error: {data}")
    return data.get("data") or []  # список офферов

# ---------- ФИЛЬТРЫ ----------

def match_offer(
    offer: dict,
    *,
    skin: Optional[str] = None,
    price: Optional[float] = None,
    quality: Optional[str] = None,
    float_value: Optional[float] = None,
    stickers: Optional[list[str]] = None,
    stattrak: Optional[bool] = None,
    rarity: Optional[str] = None,
    pattern: Optional[int] = None,
    price_tolerance: float = 0.03,
) -> bool:
    """
    Проверяет, подходит ли оффер под заданные параметры.
    None / 0 = параметр игнорируется.
    price_tolerance = допускаемое отклонение цены (например, 3%).
    """
    name = offer.get("market_hash_name", "")
    extra = offer.get("extra") or {}
    offer_price = float(offer.get("price", 0))

    # 1. Скин (строгое совпадение имени)
    if skin is not None and skin.strip() and name != skin:
        return False

    # 2. Цена с допуском
    if price not in (None, 0):
        if not (price * (1 - price_tolerance) <= offer_price <= price * (1 + price_tolerance)):
            return False

    # 3. Качество (Field-Tested, Factory New, и т.п.) — парсим из названия
    if quality not in (None, "", "0"):
        if f"({quality})" not in name:
            return False

    # 4. Флоат
    offer_float = extra.get("float")
    if float_value not in (None, 0):
        try:
            offer_float = float(offer_float) if offer_float is not None else None
        except ValueError:
            offer_float = None
        if offer_float is None or abs(offer_float - float_value) > 1e-4:
            return False

    # 5. Наклейки
    if stickers:
        offer_stickers = extra.get("stickers") or []
        offer_sticker_names = {s.get("name") for s in offer_stickers if isinstance(s, dict)}
        for st in stickers:
            if st and st not in offer_sticker_names:
                return False

    # 6. StatTrak
    if stattrak is not None:
        has_st = "StatTrak" in name
        if has_st != stattrak:
            return False

    # 7. Редкость (TODO: нужно отдельное поле/база; пока можно пропустить)
    if rarity not in (None, "", "0"):
        # пример: редкость можно было бы брать из своего словаря по market_hash_name
        return False

    # 8. Паттерн (paintseed)
    if pattern not in (None, 0):
        offer_pattern = extra.get("paintseed") or extra.get("pattern")
        try:
            offer_pattern = int(offer_pattern)
        except (TypeError, ValueError):
            offer_pattern = None
        if offer_pattern != pattern:
            return False

    return True

# ---------- ПОИСК С УЧЁТОМ РЕЖИМА ----------

def strict_search(
    skin: str,
    price: float = 0,
    quality: Optional[str] = None,
    float_value: float = 0,
    stickers: Optional[list[str]] = None,
    stattrak: Optional[bool] = None,
    rarity: Optional[str] = None,
    pattern: int = 0,
    mode: int = 1,
):
    """
    mode=1 — единичный запрос;
    mode=2 — опрос каждые 5 секунд до нахождения строгого совпадения.
    Если строгих нет — возвращает до 10 ближайших по цене.
    """
    stickers = stickers or []

    def one_pass() -> tuple[list[dict], list[dict]]:
        offers = fetch_offers(skin)
        if not offers:
            return [], []

        strict = [
            o for o in offers
            if match_offer(
                o,
                skin=skin,
                price=price if price else None,
                quality=quality,
                float_value=float_value if float_value else None,
                stickers=stickers,
                stattrak=stattrak,
                rarity=rarity,
                pattern=pattern if pattern else None,
            )
        ]

        # ближайшие по цене (если строгих нет)
        if strict:
            return strict, []

        if price:
            offers_sorted = sorted(offers, key=lambda o: abs(float(o.get("price", 0)) - price))
        else:
            offers_sorted = sorted(offers, key=lambda o: float(o.get("price", 0)))

        closest = offers_sorted[:10]
        return [], closest

    if mode == 1:
        strict, closest = one_pass()
        return strict, closest

    # mode == 2: пинг каждые 5 секунд
    while True:
        strict, closest = one_pass()
        if strict:
            return strict, []
        print("Строгих совпадений нет, ближайшие офферы есть. Ждём 5 секунд...")
        time.sleep(5)


# ---------- ССЫЛКИ НА ПРЕДМЕТ И ФОРМАТ ВЫВОДА ----------

from urllib.parse import quote


def offer_url(offer: dict) -> str:
    """
    Строит ссылку на страницу предмета на Market.CSGO.
    Использует market_hash_name и class (как id).
    """
    name = offer.get("market_hash_name", "")
    class_id = offer.get("class") or offer.get("classid")

    if not name:
        return "https://market.csgo.com/"

    encoded_name = quote(name, safe="")  # кодируем пробелы, скобки и т.п.

    if class_id:
        return f"https://market.csgo.com/ru/{encoded_name}?id={class_id}"
    else:
        # fallback – поиск по имени
        return f"https://market.csgo.com/ru/?search={encoded_name}"



def format_offers_list(title: str, offers: list[dict]) -> str:
    if not offers:
        return f"{title}\nНет результатов."
    lines = [title]
    for o in offers:
        name = o.get("market_hash_name")
        price = o.get("price")
        count = o.get("count")
        url = offer_url(o)
        lines.append(f"{name} | цена: {price} | кол-во: {count} | {url}")
    return "\n".join(lines)

# ---------- ПРИМЕР ИСПОЛЬЗОВАНИЯ ----------

def main():
    # пример: строгий поиск по имени и цене, остальное игнорируем
    mode = int(input("Режим (1 - разовый, 2 - пинг каждые 5 сек): ").strip() or "1")

    skin = input("Скин (market_hash_name): ").strip()
    price = float(input("Цена (0 - игнорировать): ").strip() or "0")
    quality = input("Качество (Factory New / Field-Tested и т.п., пусто - игнор): ").strip() or None
    float_value = float(input("Флоат (0 - игнорировать): ").strip() or "0")
    stattrak_in = input("StatTrak? (1 - да, 0 - нет, пусто - игнор): ").strip()
    stattrak = None
    if stattrak_in == "1":
        stattrak = True
    elif stattrak_in == "0":
        stattrak = False

    # для упрощения: одну наклейку строкой; можно расширить до списка
    sticker = input("Наклейка (точное имя, пусто - игнор): ").strip()
    stickers = [sticker] if sticker else []

    pattern = int(input("Паттерн (0 - игнор): ").strip() or "0")

    strict, closest = strict_search(
        skin=skin,
        price=price,
        quality=quality,
        float_value=float_value,
        stickers=stickers,
        stattrak=stattrak,
        rarity=None,   # пока не используем
        pattern=pattern,
        mode=mode,
    )

    if strict:
        print(format_offers_list("Строгие совпадения:", strict))
    else:
        print(format_offers_list("Ближайшие совпадения:", closest))


if __name__ == "__main__":
    main()
