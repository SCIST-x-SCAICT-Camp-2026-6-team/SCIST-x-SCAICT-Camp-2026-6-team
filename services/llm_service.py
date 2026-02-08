# services/llm_service.py
import google.generativeai as genai
import random

# services/llm_service.py

class LLMService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.is_online = False
        
        if self.api_key and self.api_key != "API_KEY":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                
                # [核心修正] 根據診斷結果，改用你 Key 支援的最新模型
                # 注意：名稱需與診斷清單一致，通常建議不帶 models/ 前綴試試
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                
                self.is_online = True
            except Exception as e:
                print(f"初始化模型失敗: {e}")
                self.is_online = False

    def generate_itinerary_summary(self, raw_data: dict):
        if not self.is_online:
            return "(AI 暫時離線) 請檢查模型設定。"

        try:
            prompt = f"你是導遊，請為{raw_data.get('county')}旅遊寫一段30字短評。"
            # 使用 Gemini 2.5 的生成能力
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            # 防禦性處理：如果 2.5 也失敗，嘗試 2.0
            return f"(AI 服務連線失敗) 建議參考下方推薦行程。"