# services/itinerary_agent.py

class ItineraryAgent:
    def __init__(self, repository, llm_service):
        """
        初始化 Agent
        :param repository: 負責資料讀取的實例 (TravelRepository)
        :param llm_service: 負責 AI 文案生成的實例 (LLMService)
        """
        self.repo = repository
        self.llm = llm_service

    def generate_trip(self, county: str) -> dict:
        """
        根據縣市名稱生成完整的旅遊規劃
        """
        # 1. 取得資料 (遵循防禦性編程，確保回傳至少是空列表)
        hotels = self.repo.get_hotels(county) or []
        attractions = self.repo.get_attractions(county) or []

        # 2. 初始化變數 (修正截圖中的變數未定義警告)
        # 提供預設值以防該縣市完全沒有資料
        selected_hotel = {
            "name": "目前該區暫無推薦住宿",
            "price_twd": 0,
            "address": "請聯繫客服確認",
            "price_text": "TWD 0"
        }
        selected_spots = []

        # 3. 核心邏輯：篩選飯店與景點
        if hotels:
            # 這裡可以實作更複雜的 SOLID 策略模式來篩選最合適的飯店
            # 目前先採 TDD 快速通關：取第一筆
            selected_hotel = hotels[0]

        if attractions:
            # 預設取前 3 個景點作為行程
            selected_spots = attractions[:3]

        # 4. 組裝原始資料包 (準備交給 LLM 加工)
        raw_data = {
            "status": "success" if (hotels or attractions) else "no_data",
            "county": county,
            "hotel": selected_hotel,
            "itinerary": selected_spots
        }

        # 5. AI 加工：生成領隊建議 (呼叫你在 LLMService 補齊的方法)
        # 即使 LLM 失敗，也要確保程式能回傳基本資料
        try:
            raw_data["ai_summary"] = self.llm.generate_itinerary_summary(raw_data)
        except AttributeError:
            raw_data["ai_summary"] = "(AI 服務尚未就緒) 祝您旅途愉快！"
        except Exception as e:
            raw_data["ai_summary"] = f"(AI 生成發生錯誤) {str(e)}"

        return raw_data