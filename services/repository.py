# services/repository.py
import json

class TravelRepository:
    def __init__(self):
        self.hotels = []
        self.attractions = []
        
        try:
            # 處理飯店
            with open('data/hotels.json', 'r', encoding='utf-8') as f:
                self.hotels = self._process_json_data(json.load(f))

            # 處理景點 (現在能正確處理你貼出的格式了)
            with open('data/attractions.json', 'r', encoding='utf-8') as f:
                self.attractions = self._process_json_data(json.load(f))
                
        except Exception as e:
            print(f"[Error] Repository Init Failed: {e}")

    def _process_json_data(self, data):
        """
        統一處理邏輯：
        1. 如果有 'results'，代表是飯店那種按縣市分組的格式。
        2. 如果有 'items' 且無 'results'，代表是景點這種直接扁平化的格式。
        """
        flattened = []
        
        # 格式 A: { "results": [ { "county": "...", "items": [...] } ] }
        if isinstance(data, dict) and "results" in data:
            for group in data["results"]:
                county_name = group.get("county")
                for item in group.get("items", []):
                    item["county"] = county_name
                    flattened.append(item)
            return flattened
            
        # 格式 B: { "items": [ { "name": "...", "county": "..." } ] }
        elif isinstance(data, dict) and "items" in data:
            return data["items"] # 這裡已經自帶 county 了，直接回傳 list
            
        # 格式 C: 本身就是 list
        elif isinstance(data, list):
            return data
            
        return []

    def get_hotels(self, county):
        return [h for h in self.hotels if h.get('county') == county]

    def get_attractions(self, county):
        # 修正後的 self.attractions 會是一個 dict 列表，不再報 AttributeError
        return [a for a in self.attractions if a.get('county') == county]