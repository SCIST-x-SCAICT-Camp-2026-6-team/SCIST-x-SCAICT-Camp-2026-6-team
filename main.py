# main.py
import os
from dotenv import load_dotenv
from services.repository import TravelRepository
from services.llm_service import LLMService
from services.itinerary_agent import ItineraryAgent

def get_itinerary_app():
    # 1. 載入環境變數
    # 建議加上 override=True，確保在開發過程中修改 .env 後能即時生效
    load_dotenv(override=True)
    
    # 修正點：不要提供 "YOUR_API_KEY" 作為預設值，這樣 LLMService 才能正確判斷「無 Key」狀態
    api_key = os.getenv("GEMINI_API_KEY")

    # 2. 初始化底層服務
    repo = TravelRepository()
    llm = LLMService(api_key=api_key)

    # 3. 初始化 Agent
    agent = ItineraryAgent(repository=repo, llm_service=llm)

    return agent, llm