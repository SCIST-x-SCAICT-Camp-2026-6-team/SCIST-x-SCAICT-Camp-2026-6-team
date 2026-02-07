# backend.py
import time
import random

def get_travel_plan(destination, days, budget):
    """
    這是後端演算法的入口函數。
    參數:
        destination (str): 目的地
        days (int): 天數
        budget (int): 預算
       
    回傳:
        dict: 包含行程的字典資料
    """
    print(f"模擬中: 正在規劃去 {destination} 的行程...")
    # 模擬後端正在瘋狂運算 (Agent 思考中...)    
    time.sleep(1.5) 
    
    base_lat = 25.04  # 緯度
    base_lon = 121.50 # 經度
    # 這裡目前是寫死的假資料 (Mock)，
    # 以後後端只要改這個函數的內容，接上他們的爬蟲/演算法就好
    return {
        "target_style": f"針對 {destination} 的深度旅遊",
        "total_cost": budget - random.randint(100, 1000), # 假裝算了一個預算
        "itinerary": [
            {
                "day_title": f"Day {i+1}: {destination} 探索之旅",
                "activities": [
                    "09:00 - 飯店出發",
                    f"10:30 - {destination} 知名景點 A",
                    "12:30 - 在地美食午餐",
                    "15:00 - 文創園區逛逛",
                    "18:00 - 夜市覓食"
                ],
                "spots": [
                    {
                        "name": f"{destination} 景點 A", 
                        "lat": base_lat + random.uniform(-0.05, 0.05), 
                        "lon": base_lon + random.uniform(-0.05, 0.05)
                    },
                    {
                        "name": "在地美食", 
                        "lat": base_lat + random.uniform(-0.05, 0.05), 
                        "lon": base_lon + random.uniform(-0.05, 0.05)
                    }
                ]
            } for i in range(days) # 根據天數自動產生幾天的行程
        ]
    }