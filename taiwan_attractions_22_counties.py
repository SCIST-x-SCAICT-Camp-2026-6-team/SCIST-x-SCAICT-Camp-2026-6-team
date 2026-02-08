import argparse
import json
import re
from collections import defaultdict
from typing import Any, Dict, List

import requests


SOURCE_URL = "https://media.taiwan.net.tw/XMLReleaseALL_public/scenic_spot_C_f.json"


def get_taiwan_22_counties() -> List[str]:
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


def normalize_text(s: str) -> str:
    return (s or "").strip().replace("台", "臺")


def infer_county(region: str, addr: str) -> str:
    region_n = normalize_text(region)
    addr_n = normalize_text(addr)
    counties = get_taiwan_22_counties()
    if region_n in counties:
        return region_n
    for c in counties:
        if c in addr_n:
            return c
    return ""


def infer_area(town: str, addr: str) -> str:
    town = (town or "").strip()
    if town:
        return town
    addr = (addr or "").strip()
    m = re.search(r"([^\s]{2,4}[區鄉鎮市])", addr)
    return m.group(1) if m else ""


def load_attractions() -> List[Dict[str, Any]]:
    r = requests.get(SOURCE_URL, timeout=120)
    obj = json.loads(r.content.decode("utf-8-sig"))
    return obj["XML_Head"]["Infos"]["Info"]


def build_outputs(raw_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    counties = get_taiwan_22_counties()
    county_set = set(counties)

    flat: List[Dict[str, Any]] = []
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for it in raw_items:
        county = infer_county(it.get("Region", ""), it.get("Add", ""))
        if county not in county_set:
            continue

        row = {
            "id": it.get("Id"),
            "name": it.get("Name"),
            "county": county,
            "area": infer_area(it.get("Town", ""), it.get("Add", "")),
            "address": (it.get("Add") or "").strip(),
            "lat": it.get("Py"),
            "lng": it.get("Px"),
            "open_time": it.get("Opentime"),
            "tel": it.get("Tel"),
            "website": it.get("Website"),
        }
        flat.append(row)
        grouped[county].append(row)

    for c in counties:
        grouped.setdefault(c, [])

    grouped_list = [{"county": c, "count": len(grouped[c]), "spots": grouped[c]} for c in counties]

    return {
        "source": SOURCE_URL,
        "total_spots": len(flat),
        "county_count": len(counties),
        "flat": flat,
        "grouped": grouped_list,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flat-output", default="taiwan_attractions_22_counties_flat.json")
    parser.add_argument("--grouped-output", default="taiwan_attractions_22_counties_grouped.json")
    args = parser.parse_args()

    raw_items = load_attractions()
    out = build_outputs(raw_items)

    with open(args.flat_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": out["source"],
                "total_spots": out["total_spots"],
                "county_count": out["county_count"],
                "items": out["flat"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(args.grouped_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": out["source"],
                "total_spots": out["total_spots"],
                "county_count": out["county_count"],
                "counties": out["grouped"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"done flat={args.flat_output}")
    print(f"done grouped={args.grouped_output}")
    print(f"total_spots={out['total_spots']}")
    for row in out["grouped"]:
        print(f"{row['county']}: {row['count']}")


if __name__ == "__main__":
    main()
