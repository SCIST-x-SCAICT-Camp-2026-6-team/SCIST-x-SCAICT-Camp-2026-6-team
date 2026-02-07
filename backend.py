# backend.py
import os
import json
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_travel_plan(destination: str, days: int, budget: int):
    # 1. 讀取飯店資料 JSON
    try:
        with open('trip_hotels_taiwan_all_counties.json', 'r', encoding='utf-8') as f:
            hotel_data = json.load(f)
    except FileNotFoundError:
        return {"error": "找不到飯店資料庫檔案"}

    # 2. 構建 Prompt：嚴格要求模型僅使用 JSON 內的資料
    # 我們將整個 JSON 內容（或篩選後的縣市內容）餵給模型
    prompt = f"""
    你是一位專業旅遊規劃師。請根據以下提供的飯店資料 JSON，為前往「{destination}」的旅客規劃行程。
    
    【限制條件】：
    1. 嚴禁使用網路搜尋，只能使用提供的 JSON 內容。
    2. 請在回傳的 JSON 中，特別列出 10 筆建議飯店（若該縣市資料不足，請從鄰近縣市挑選並說明）。
    3. 行程規劃需符合預算 {budget} 元。
    
    【提供資料】：
    {json.dumps(hotel_data, ensure_ascii=False)}

    請回傳純 JSON 格式：
    {{
      "target_style": "風格描述",
      "recommended_hotels": ["飯店 A (價格)", "飯店 B (價格)", ...], 
      "itinerary": [...]
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        # 清洗與解析 JSON
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw_text)
        
    except Exception as e:
        print(f"處理失敗: {e}")
        return {"error": str(e)}