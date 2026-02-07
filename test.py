# test_real_backend.py
import unittest
from backend import get_travel_plan

class TestRealAI(unittest.TestCase):
    def test_api_call_returns_valid_structure(self):
        # 實際呼叫 (需聯網)
        result = get_travel_plan("台中市", 1, 2000)
        
        # 驗證結構是否符合前端規範
        self.assertIn("itinerary", result)
        self.assertTrue(len(result["itinerary"]) >= 1)
        print("✅ AI 串接測試成功！")

if __name__ == '__main__':
    unittest.main()