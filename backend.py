import requests

def get_travel_plan(destination, days, budget):
    base_url = "http://localhost:8000/api/v1"
    user_id = "direct_test_001"
    
    # 這裡必須是純 Dictionary，requests 會自動轉成 JSON
    payload = {
        "user_id": user_id,
        "preferences": {
            "destination": destination,
            "days": days,
            "budget": budget
        }
    }
    
    try:
        # 1. 更新資料庫
        requests.post(f"{base_url}/upload", json=payload)
        # 2. 獲取行程
        response = requests.get(f"{base_url}/agent/generate/{user_id}")
        return response.json()
    except Exception:
        return {"status": "error", "message": "連線失敗"}