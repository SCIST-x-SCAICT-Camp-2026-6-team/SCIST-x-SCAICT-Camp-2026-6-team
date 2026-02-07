import streamlit as st
import pandas as pd
import backend  # 引用上面的 backend.py

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI 旅遊 Agent", layout="wide")

# --- CSS 樣式 ---
st.markdown("""
<style>
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #F0F8FF;
        border: 2px solid #87CEFA;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State ---
if 'travel_result' not in st.session_state:
    st.session_state['travel_result'] = None

# --- 3. 顯示函數 ---
def display_itinerary(data):
    target_style = data.get('target_style', '未定義')
    st.info(f"🎯 核心風格：{target_style}")
    
    map_data = [] 
    if "itinerary" in data:
        for i, day in enumerate(data['itinerary']):
            title = day.get('day_title', f"Day {i+1}")
            with st.expander(f"🗓️ {title}", expanded=(i==0)):
                for activity in day.get('activities', []):
                    st.write(f"📍 {activity}")
                for spot in day.get('spots', []):
                    map_data.append({"lat": spot['lat'], "lon": spot['lon']})
    
    if map_data:
        st.divider()
        st.subheader("🗺️ 路線地圖")
        st.map(pd.DataFrame(map_data))

    st.metric("預估總花費", f"${data.get('total_cost', 0):,}")

# --- 4. 主介面 ---
st.title("🤖 台灣旅遊行程規劃 Agent")

with st.sidebar:
    st.header("Step 1: 輸入需求")
    city_list = ["台北市", "新北市", "台中市", "台南市", "高雄市", "花蓮縣", "台東縣"]
    destination = st.selectbox("目的地", city_list)
    days = st.slider("天數", 1, 10, 3)
    budget = st.number_input("預算上限", value=5000, step=1000)
    st.divider()
    run_btn = st.button("🚀 開始規劃", type="primary")

# --- 5. 核心排版區 ---
result_col, agent_col = st.columns([2, 1])

with agent_col:
    st.subheader("💬 Agent 思考區")
    with st.container(border=True):
        st.chat_message("assistant").write("準備好隨時為您規劃！")
        if st.session_state['travel_result']:
             d_len = len(st.session_state['travel_result']['itinerary'])
             st.chat_message("assistant").write(f"已經為您生成 {d_len} 天的行程囉！")

with result_col:
    st.subheader(f"📅 {destination} 行程表")
    if run_btn:
        with st.spinner("呼叫 Agent 中..."):
            # 呼叫實質 AI 後端
            result_data = backend.get_travel_plan(destination, days, budget)
            st.session_state['travel_result'] = result_data
            st.success("規劃完成！")

    current_data = st.session_state['travel_result']
    if current_data:
        display_itinerary(current_data)
        with st.expander("🔧 開發者模式"):
            st.json(current_data)
    else:
        st.info("👈 請點擊左側按鈕開始")