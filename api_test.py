import requests

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


def search_item_by_hash_name(hash_name: str):
    """
    Ищет предмет по market_hash_name и возвращает данные с маркета.
    """
    url = f"{BASE_URL}/search-item-by-hash-name"
    params = {
        "hash_name": hash_name,
        "currency": "RUB",  # при необходимости поменяй
    }
    
    resp = session.get(url, params=params, timeout=10)
    print("STATUS:", resp.status_code)
    print("TEXT:", resp.text[:300])
    resp.raise_for_status()

    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"API error: {data}")

    # ответ по доке:
    # { "success": true, "currency": "USD", "data": [ {...}, {...} ] }
    return data.get("data") or []


def main():
    target_name = "AK-47 | Case Hardened (Field-Tested)"
    offers = search_item_by_hash_name(target_name)

    if not offers:
        print("Предложений по этому предмету нет")
        return

    # Возьмём первое предложение
    first = offers[1]
    price = first.get("price")
    count = first.get("count")

    print("Название:", first.get("market_hash_name"))
    print("Цена:", price)
    print("Кол-во на продаже:", count)


if __name__ == "__main__":
    main()
