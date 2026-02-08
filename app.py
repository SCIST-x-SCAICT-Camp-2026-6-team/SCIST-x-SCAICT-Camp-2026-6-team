import streamlit as st
import datetime
from main import get_itinerary_app

# --- 1. 頁面配置與 CSS 樣式 ---
st.set_page_config(page_title="旅遊行程規劃 Agent", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        border: none;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4251;
    }
    .streamlit-expanderHeader {
        background-color: #1e2130;
        border-radius: 5px;
    }
    /* AI 建議區塊專用樣式 */
    .ai-box {
        background-color: #1a2a3a;
        padding: 20px;
        border-left: 5px solid #00d4ff;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化後端 (包含 LLM 注入) ---
# 確保 main.py 裡的 get_itinerary_app() 現在會回傳 (agent, llm)
agent, llm = get_itinerary_app()

# --- 3. Sidebar 介面 ---
with st.sidebar:
    st.header("在此輸入需求")
    
    selected_county = st.selectbox("目的地", [
        "新北市", "臺北市", "桃園市", "台中市", "台南市", "高雄市", 
        "基隆市", "新竹市", "嘉義市", "宜蘭縣", "新竹縣", "苗栗縣", 
        "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣"
    ])
    
    travel_date = st.date_input("出發日期", datetime.date.today())
    budget = st.number_input("預算上限", min_value=0, value=5000, step=500)
    start_btn = st.button("🚀 開始規劃")

# --- 4. 主畫面佈局 ---
col_main, col_thought = st.columns([2, 1])

with col_thought:
    st.subheader("Agent 思考區")
    thought_box = st.empty()
    thought_box.warning("🤖 準備好隨時為您規劃！")

with col_main:
    st.title("旅遊行程規劃 Agent")
    
    if start_btn:
    # 顯示隨機的思考文案
        current_thought = llm.generate_thoughts()
        thought_box.info(current_thought)
    
    with st.spinner("AI 正在規劃您的完美行程..."):
        # 呼叫 Agent 進行實際規劃
        result = agent.generate_trip(selected_county)
        
        if result and result.get("status") == "success":
            st.subheader(f"推薦的 {selected_county} 行程表")
            st.caption(f"📅 預定出發日期：{travel_date} | 💰 預算設定：TWD {budget}")
            
            # --- [AI Agent 核心功能：領隊建議] ---
            if "ai_summary" in result:
                st.markdown(f"""
                <div class="ai-box">
                    <h4 style='margin-top:0;'>✨ AI 領隊建議</h4>
                    {result['ai_summary']}
                </div>
                """, unsafe_allow_html=True)
            
            # 顯示住宿花費
            # --- 顯示住宿與行程 ---
            hotel = result.get("hotel", {})
            
            # [修正點] 使用防禦性取值，優先找 price_twd，次之找 price，找不到則顯示 0
            # 這是為了對應不同資料來源可能有的欄位差異 (price vs price_twd)
            raw_price = hotel.get('price_twd') or hotel.get('price') or 0
            
            # 使用千分位格式化金額，提升 UI 質感
            display_price = f"TWD {raw_price:,}" if isinstance(raw_price, (int, float)) else f"TWD {raw_price}"
            
            # 顯示住宿預估花費
            st.metric(label="住宿預估花費", value=display_price)
            
            # 推薦住宿區塊
            hotel_name = hotel.get('name', '未找到合適住宿')
            st.success(f"🏨 推薦住宿：{hotel_name}")
            
            # 使用 .get 提供預設值避免 KeyError
            hotel_address = hotel.get('address') or hotel.get('hotel_address') or '資料更新中'
            st.write(f"📍 地址：{hotel_address}")
            
            st.write("---")
            st.subheader("📍 推薦行程路線")

            if result and result.get("status") == "success":
                st.subheader(f"推薦的 {selected_county} 行程表")
                st.caption(f"📅 預定出發日期：{travel_date} | 💰 預算設定：TWD {budget}")
            
            # 1. AI 領隊建議
            ai_content = result.get('ai_summary', '(AI 忙碌中) 祝您旅途愉快！')
            st.markdown(f"""
                <div class="ai-box">
                    <h4 style='margin-top:0;'>✨ AI 領隊建議</h4>
                    {ai_content}
                </div>
            """, unsafe_allow_html=True)
            
            # 2. 住宿資訊 (防禦性取值再加強)
            hotel = result.get("hotel", {})
            # 優先找 price_twd, 次之 price，都沒就 0
            raw_price = hotel.get('price_twd') or hotel.get('price') or 0
            
            col_metric, col_hotel = st.columns([1, 2])
            with col_metric:
                st.metric(label="住宿預估花費", value=f"TWD {raw_price:,}")
            
            with col_hotel:
                st.success(f"🏨 推薦住宿：{hotel.get('name', '未找到飯店')}")
                st.write(f"📍 {hotel.get('address', '地址更新中')}")
            
            st.divider()
            
            # 3. 路線清單 (檢查行程是否存在)
            st.subheader("📍 推薦行程路線")
            itinerary = result.get("itinerary", [])
            
            if not itinerary:
                st.info("目前該區域暫無推薦景點，建議調整目的地。")
            else:
                for i, spot in enumerate(itinerary):
                    # 使用 columns 讓排版更精緻
                    with st.expander(f"第 {i+1} 站：{spot.get('name', '未知景點')}", expanded=(i==0)):
                        col_text, col_tag = st.columns([3, 1])
                        with col_text:
                            st.write(f"🏠 地址：{spot.get('address', '請參閱地圖導航')}")
                        with col_tag:
                            st.info(f"🚩 順序 {i+1}")
            
            thought_box.success("✅ 行程規劃完成！")
            
            # 行程詳細內容
            for i, spot in enumerate(result.get("itinerary", [])):
                with st.expander(f"第 {i+1} 站：{spot['name']}", expanded=True):
                    st.write(f"🏠 地址：{spot.get('address', '請參閱地圖導航')}")
            
            thought_box.success("✅ 行程規劃完成！")
        else:
            st.error("⚠️ 資料格式異常，請檢查後端回傳結構。")
            thought_box.error("❌ 規劃中斷")

# --- 5. 開發者模式 ---
with st.expander("🔍 開發者模式 (查看 Agent 回傳 JSON)"):
    if 'result' in locals():
        st.json(result)