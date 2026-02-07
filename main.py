import streamlit as st
import time
import backend 
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI 旅遊 Agent", layout="wide")

# --- CSS 樣式優化 (加強版) ---
st.markdown("""
<style>
    /* 1. 網頁背景：莫蘭迪冷灰 (改掉原本的米色 #FFFBF0) */
    .stApp {
        background-color: #F2F4F8; 
    }

    /* 2. 側邊欄背景：稍微深一點的灰 */
    [data-testid="stSidebar"] {
        background-color: #E8ECF1;
    }

    /* 3. Agent 對話框：強制長高 + 莫蘭迪配色 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; /* 對話框變純白，比較乾淨 */
        border: 2px solid #B4C6D0; /* 邊框：莫蘭迪藍灰 */
        border-radius: 15px;
        padding: 20px;
        
        /* [關鍵修正] 改用 px (像素) 強制撐開！ */
        /* 不管內容多少，它永遠都會有 750px 那麼高 */
        min-height: 800pxortant; 
    }
    
    /* 調整成功訊息 */
    .stAlert {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 初始化 Session State ---
if 'travel_result' not in st.session_state:
    st.session_state['travel_result'] = None

# --- 3. 顯示函數 ---
def display_itinerary(data):
    target_style = data.get('target_style', '未定義')
    st.info(f"核心風格：{target_style}")
    
    map_data = [] 
    if "itinerary" in data:
        for i, day in enumerate(data['itinerary']):
            title = day.get('day_title', f"Day {i+1}")
            with st.expander(f" {title}", expanded=(i==0)):
                for activity in day.get('activities', []):
                    st.write(f"📍 {activity}")
                for spot in day.get('spots', []):
                    map_data.append([spot['lat'], spot['lon']])
    else:
        st.warning("⚠️ 資料格式異常")

    if map_data:
        st.divider()
        df_map = pd.DataFrame(map_data, columns=['lat', 'lon'])
        #st.map(df_map)
        if map_data:
         st.divider()
        st.subheader("🗺️ 路線地圖 (互動式)")

        # 1. 計算地圖中心點 (取所有景點的平均座標，讓地圖一開始就置中)
        df_map = pd.DataFrame(map_data, columns=['lat', 'lon'])
        center_lat = df_map['lat'].mean()
        center_lon = df_map['lon'].mean()

        # 2. 建立地圖物件
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # 定義每天的顏色，讓地圖看起來更繽紛
        colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred']

        # 3. 畫出景點與路線
        for day_idx, day in enumerate(data['itinerary']):
            # 取出這一天的所有座標點
            day_points = []
            day_color = colors[day_idx % len(colors)] # 顏色循環使用

            for spot in day.get('spots', []):
                lat, lon = spot['lat'], spot['lon']
                name = spot['name']
                day_points.append([lat, lon])

                # 建立標記 (Marker)
                folium.Marker(
                    location=[lat, lon],
                    popup=f"Day {day_idx+1}: {name}", # 點擊跳出名稱
                    tooltip=name, # 滑鼠移過去顯示名稱
                    icon=folium.Icon(color=day_color, icon="info-sign")
                ).add_to(m)

            # 建立連線 (把這一天的點連起來)
            if len(day_points) > 1:
                folium.PolyLine(
                    day_points,
                    color=day_color,
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Day {day_idx+1} 路線"
                ).add_to(m)

        # 4. 在 Streamlit 中渲染地圖
        st_folium(m, width=700, height=500)

    total = data.get('total_cost', 0)
    st.metric("預估總花費", f"${total:,}")

# --- 4. 主介面 ---
   

with st.sidebar:
    st.header("在此輸入需求")
    city_list = ["台北市", "新北市", "台中市", "台南市", "高雄市", "花蓮縣", "台東縣"]
    destination = st.selectbox("目的地", city_list)
    days = st.slider("天數", 1, 10, 3)
    budget = st.number_input("預算上限", value=5000, step=1000)
    st.divider()
    run_btn = st.button("🚀 開始規劃", type="primary")



# --- 5. 核心排版區 (這裡就是關鍵！) ---

# [關鍵] 先切好左右兩欄！不要被按鈕影響！
result_col, agent_col = st.columns([2, 1])

# --- 先處理右邊 (Agent) ---
# 這樣它就會永遠固定在右邊，不會被左邊的運算擠下去
with agent_col:
    st.subheader("Agent 思考區")
    with st.container(border=True, height=1000):
        st.chat_message("assistant").write("準備好隨時為您規劃！")
        
        # 顯示狀態
        if st.session_state['travel_result']:
             d_len = len(st.session_state['travel_result']['itinerary'])
             st.chat_message("assistant").write(f"已經為您生成 {d_len} 天的行程囉！")

# --- 再處理左邊 (結果與運算) ---
with result_col:
    # 標題先出來
    st.title("旅遊行程規劃 Agent")
    st.subheader(f"推薦的{destination} 行程表")

    # 運算邏輯放在「左欄裡面」
    if run_btn:
        with st.spinner("呼叫 Agent 中..."):
            result_data = backend.get_travel_plan(destination, days, budget)
            st.session_state['travel_result'] = result_data
            st.toast('🎉 規劃完成！正在為您產生路線地圖...', icon='✅')
            time.sleep(1) # 讓它停留一下
            st.toast('🗺️ 地圖載入完畢！', icon='🚀')


    # 顯示結果
    current_data = st.session_state['travel_result']
    if current_data:
        display_itinerary(current_data)
        st.divider() # 畫一條分隔線，比較好看
                    
        itinerary_text = f"【{destination} {days} 天深度旅遊行程】\n"
        itinerary_text += f"預估總花費: ${current_data['total_cost']:,}\n\n"
                    
        for day in current_data['itinerary']:
                        itinerary_text += f"■ {day['day_title']}\n"
                        for act in day['activities']:
                            itinerary_text += f"  - {act}\n"
                        itinerary_text += "\n"
                    

        st.download_button(
                        label="📥 下載行程表 (.txt)",
                        data=itinerary_text,
                        file_name=f"{destination}_travel_plan.txt",
                        mime="text/plain",
                        help="點擊下載將行程存成文字檔"
                    )
        with st.expander("開發者模式"):
            st.json(current_data)
    else:
        st.info("請點擊左側按鈕開始")