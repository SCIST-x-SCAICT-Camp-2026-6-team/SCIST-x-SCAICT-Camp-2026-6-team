# backend.py
import os
import json
from google import genai  # 使用最新的 SDK
from dotenv import load_dotenv

load_dotenv()

# 初始化客戶端
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_travel_plan(destination: str, days: int, budget: int):
    # 這裡加入真正的 AI 呼叫
    prompt = f"規劃 {destination} 的 {days} 天旅遊，預算 {budget}。請只回傳 JSON。"
    
    try:
        # 真正送出請求
        response = client.models.generate_content(
    model="gemini-2.0-flash",  
    contents=prompt
)
        
        # 假設 AI 回傳的是純文字 JSON
        return json.loads(response.text)
        
    except Exception as e:
        # TDD 精神：如果沒接 API，這裡一定會噴錯，讓測試變成紅燈
        print(f"API 呼叫失敗: {e}")
        raise e