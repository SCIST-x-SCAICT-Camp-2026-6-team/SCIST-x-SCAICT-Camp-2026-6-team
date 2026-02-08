import argparse
import html
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests


USER_AGENT = "Mozilla/5.0"
BASE_LIST_URL = "https://tw.trip.com/hotels/list"
BASE_DETAIL_URL = "https://tw.trip.com/hotels/detail/?hotelid={hotel_id}"

LOGGER = logging.getLogger("trip_taiwan_scraper")


def get_all_taiwan_counties_cities() -> List[str]:
    return [
        "基隆市",
        "新北市",
        "臺北市",
        "桃園市",
        "新竹市",
        "新竹縣",
        "苗栗縣",
        "臺中市",
        "彰化縣",
        "南投縣",
        "雲林縣",
        "嘉義市",
        "嘉義縣",
        "臺南市",
        "高雄市",
        "屏東縣",
        "宜蘭縣",
        "花蓮縣",
        "臺東縣",
        "澎湖縣",
        "金門縣",
        "連江縣",
    ]


def get_known_trip_city_ids() -> Dict[str, int]:
    # 來自 Trip.com 台灣省份頁可直接解析到的城市 id
    return {
        "臺北市": 617,
        "台北市": 617,
        "新北市": 7662,
        "桃園市": 7570,
        "臺中市": 3849,
        "台中市": 3849,
        "臺南市": 3847,
        "台南市": 3847,
        "高雄市": 720,
        "宜蘭縣": 7614,
        "南投縣": 7524,
        "嘉義市": 5152,
        "臺東縣": 3848,
        "台東縣": 3848,
        "基隆市": 7810,
        "新竹市": 3845,
        "新竹縣": 669328,
        "苗栗縣": 7809,
        "彰化縣": 7811,
        "雲林縣": 7523,
        "嘉義縣": 650358,
        "屏東縣": 5589,
        "花蓮縣": 6954,
        "澎湖縣": 7805,
        "金門縣": 7203,
        "連江縣": 7808,
    }


def normalize_county_name(name: str) -> str:
    return name.replace("臺", "台")


def to_search_keyword(county_name: str) -> str:
    name = normalize_county_name(county_name).strip()
    for suffix in ("市", "縣"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def build_taiwan_city_targets() -> List[Dict[str, Any]]:
    known = get_known_trip_city_ids()
    targets: List[Dict[str, Any]] = []
    for county in get_all_taiwan_counties_cities():
        city_id = known.get(county)
        if city_id is None:
            city_id = known.get(normalize_county_name(county))
        targets.append({"county": county, "city_id": city_id})
    return targets


def _clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = " ".join(text.split())
    return text or None


def _extract_price_twd(card_html: str) -> (Optional[int], Optional[str]):
    room_price_block = re.search(
        r'class="room-price"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        card_html,
        re.I | re.S,
    )
    scope = room_price_block.group(1) if room_price_block else card_html
    numbers: List[int] = []
    for x in re.findall(r"TWD\s*([0-9,]+)", scope, re.I):
        cleaned = x.replace(",", "").strip()
        if not cleaned or not cleaned.isdigit():
            continue
        numbers.append(int(cleaned))
    if not numbers:
        return None, None
    price = min(numbers[:2]) if len(numbers) >= 2 else numbers[0]
    return price, f"TWD {price:,}"


def _parse_list_page(html_text: str, limit: int) -> List[Dict[str, Any]]:
    cards = list(re.finditer(r'data-offline-hotelId="(\d+)"', html_text, re.I))
    items: List[Dict[str, Any]] = []

    for i, m in enumerate(cards[:limit]):
        start = m.start()
        end = cards[i + 1].start() if i + 1 < len(cards) else min(len(html_text), start + 120000)
        block = html_text[start:end]

        hotel_id = int(m.group(1))
        name_match = re.search(r'class="hotelName"[^>]*>(.*?)</span>', block, re.I | re.S)
        name = _clean_text(name_match.group(1)) if name_match else None

        score = None
        score_match = re.search(r'class="score"[^>]*>\s*([0-9]+(?:\.[0-9]+)?)\s*</span>', block, re.I | re.S)
        if score_match:
            score = float(score_match.group(1))

        price_twd, price_text = _extract_price_twd(block)

        address_match = re.search(r'class="position-desc"[^>]*>(.*?)</span>', block, re.I | re.S)
        address = _clean_text(address_match.group(1)) if address_match else None

        items.append(
            {
                "hotel_id": hotel_id,
                "name": name,
                "price_twd": price_twd,
                "price_text": price_text,
                "rating": score,
                "address": address,
            }
        )

    return items


def _fetch_detail_address(session: requests.Session, hotel_id: int) -> (int, Optional[str]):
    try:
        text = session.get(BASE_DETAIL_URL.format(hotel_id=hotel_id), timeout=25).text
    except Exception:
        return hotel_id, None

    text = text.replace('\\\\\\"', '"')
    match = re.search(r'"streetAddress":"(.*?)"', text, re.S)
    return hotel_id, html.unescape(match.group(1)) if match else None


def scrape_city_hotels(
    session: requests.Session,
    county: str,
    city_id: int,
    max_hotels: int,
    detail_workers: int,
) -> Dict[str, Any]:
    params = {"city": city_id, "searchWord": to_search_keyword(county)}
    url = f"{BASE_LIST_URL}?{urlencode(params)}"
    LOGGER.info("scraping county=%s city_id=%s url=%s", county, city_id, url)
    html_text = session.get(url, timeout=30).text
    items = _parse_list_page(html_text, limit=max_hotels)

    with ThreadPoolExecutor(max_workers=detail_workers) as executor:
        futures = [executor.submit(_fetch_detail_address, session, it["hotel_id"]) for it in items]
        addr_map: Dict[int, Optional[str]] = {}
        for future in as_completed(futures):
            hid, addr = future.result()
            addr_map[hid] = addr

    for it in items:
        detail_addr = addr_map.get(it["hotel_id"])
        if detail_addr:
            it["address"] = detail_addr

    return {
        "county": county,
        "city_id": city_id,
        "query_url": url,
        "count": len(items),
        "items": items,
    }


def scrape_taiwan_hotels(
    max_hotels_per_city: int = 10,
    detail_workers: int = 5,
) -> Dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    targets = build_taiwan_city_targets()
    results: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []

    for target in targets:
        county = target["county"]
        city_id = target["city_id"]
        if city_id is None:
            LOGGER.warning("skip county=%s reason=city_id_not_configured", county)
            skipped.append({"county": county, "reason": "city_id_not_configured"})
            continue
        try:
            city_result = scrape_city_hotels(
                session=session,
                county=county,
                city_id=city_id,
                max_hotels=max_hotels_per_city,
                detail_workers=detail_workers,
            )
            LOGGER.info("done county=%s count=%s", county, city_result["count"])
            results.append(city_result)
        except Exception as exc:
            LOGGER.exception("failed county=%s city_id=%s", county, city_id)
            skipped.append({"county": county, "city_id": city_id, "reason": f"scrape_failed: {exc}"})

    total_items = sum(r["count"] for r in results)
    return {
        "total_cities_scraped": len(results),
        "total_hotels": total_items,
        "results": results,
        "skipped": skipped,
    }


def select_exact_total(data: Dict[str, Any], target_total: int) -> Dict[str, Any]:
    # 每個城市至少保留一筆，剩餘配額再依原順序補滿
    city_rows: List[Dict[str, Any]] = data.get("results", [])
    per_city_items: List[List[Dict[str, Any]]] = []
    for row in city_rows:
        items = row.get("items", [])
        # 在 item 中帶上縣市，方便扁平輸出
        tagged = []
        for it in items:
            x = dict(it)
            x["county"] = row.get("county")
            x["city_id"] = row.get("city_id")
            tagged.append(x)
        per_city_items.append(tagged)

    selected: List[Dict[str, Any]] = []
    # first pass: one per city
    for items in per_city_items:
        if items:
            selected.append(items[0])

    if len(selected) > target_total:
        selected = selected[:target_total]
    else:
        # second pass: fill remaining
        for items in per_city_items:
            for it in items[1:]:
                if len(selected) >= target_total:
                    break
                selected.append(it)
            if len(selected) >= target_total:
                break

    return {
        "target_total": target_total,
        "actual_total": len(selected),
        "unique_counties_included": sorted(list({x.get("county") for x in selected if x.get("county")})),
        "items": selected,
        "skipped": data.get("skipped", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="trip_hotels_taiwan_all_counties.json")
    parser.add_argument("--max-hotels-per-city", type=int, default=10)
    parser.add_argument("--detail-workers", type=int, default=5)
    parser.add_argument("--target-total", type=int, default=200)
    parser.add_argument("--log-file", default="trip_taiwan_scraper.log")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    level = getattr(logging, args.log_level.upper(), logging.INFO)
    LOGGER.setLevel(level)
    LOGGER.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)
    LOGGER.addHandler(sh)

    fh = logging.FileHandler(args.log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)
    LOGGER.addHandler(fh)

    LOGGER.info("start scrape target_total=%s max_hotels_per_city=%s", args.target_total, args.max_hotels_per_city)

    data = scrape_taiwan_hotels(
        max_hotels_per_city=args.max_hotels_per_city,
        detail_workers=args.detail_workers,
    )

    final_data = select_exact_total(data, target_total=args.target_total)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    LOGGER.info("output=%s selected=%s counties=%s skipped=%s", args.output, final_data["actual_total"], len(final_data["unique_counties_included"]), len(final_data["skipped"]))
    print(f"done: {args.output}")
    print(f"cities scraped: {data['total_cities_scraped']}, hotels(raw): {data['total_hotels']}")
    print(f"selected: {final_data['actual_total']}, counties included: {len(final_data['unique_counties_included'])}")
    print(f"skipped: {len(final_data['skipped'])}")


if __name__ == "__main__":
    main()
