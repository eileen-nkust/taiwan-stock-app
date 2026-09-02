import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import twstock
import calendar
from datetime import datetime, date, timedelta
from scipy.signal import find_peaks

# 1. 網頁頁面設定
st.set_page_config(
    page_title="AI 智理財：量化技術走勢與型態掃描看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 2. 自訂 CSS 美化樣式
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    h1, h2, h3, h4, h5, h6, label {
        color: #F0F6FC !important;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #8B949E;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    [data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 12px 16px;
        border-radius: 12px;
        height: 105px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #58A6FF;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700;
        color: #58A6FF !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    div.stButton > button {
        width: 100%;
        background-color: #1F6FEB !important;
        color: #FFFFFF !important;
        border: 1px solid #388BFD !important;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-size: 1.05rem !important;
        font-weight: 600;
        text-align: center !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    div.stButton > button:hover {
        background-color: #388BFD !important;
        border-color: #58A6FF !important;
        transform: translateY(-1px);
    }
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] {
        background-color: #0D1117 !important;
        color: #C9D1D9 !important;
        border-radius: 8px !important;
        border: 1px solid #30363D !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 Session State
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "df" not in st.session_state:
    st.session_state.df = None
if "detected_patterns" not in st.session_state:
    st.session_state.detected_patterns = []
if "company_name" not in st.session_state:
    st.session_state.company_name = ""

# 標頭渲染
st.markdown('<div class="main-title">AI 智理財：量化技術走勢與型態掃描看板</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">自動精準辨識經典幾何圖形，支援滑鼠滾輪自由無級縮放與雙圖動態連動。</div>', unsafe_allow_html=True)

# 自動抓取中文名稱
def get_taiwan_stock_name(stock_id):
    try:
        if stock_id in twstock.codes:
            return twstock.codes[stock_id].name
    except Exception:
        pass
    return f"股票 {stock_id}"

# K 線與幾何型態識別演算法
def detect_patterns(df):
    patterns = []
    prices = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    dates = df.index.tolist()
    n = len(prices)

    if n < 20:
        return patterns

    peaks, _ = find_peaks(highs, distance=5)
    troughs, _ = find_peaks(-lows, distance=5)

    # 1. W底
    for i in range(len(troughs) - 1):
        t1, t2 = troughs[i], troughs[i+1]
        l1, l2 = lows[t1], lows[t2]
        if abs(l1 - l2) / min(l1, l2) < 0.04 and (t2 - t1) <= 60:
            mid_peaks = [p for p in peaks if t1 < p < t2]
            if mid_peaks:
                p_mid = mid_peaks[0]
                neck_line = highs[p_mid]
                patterns.append({
                    "id": f"W底_{dates[t2]}",
                    "name": "W底 (Double Bottom)",
                    "type": "看多",
                    "date": dates[t2],
                    "skeleton_x": [dates[t1], dates[p_mid], dates[t2]],
                    "skeleton_y": [l1, neck_line, l2],
                    "skeleton_color": "#00FF7F",
                    "neck_x": [dates[t1], dates[min(t2+10, n-1)]],
                    "neck_y": [neck_line, neck_line],
                    "neck_color": "#1E90FF",
                    "annotations": [{"x": dates[t2], "y": l2, "text": "W底", "color": "#00FF7F"}]
                })

    # 2. M頭
    for i in range(len(peaks) - 1):
        p1, p2 = peaks[i], peaks[i+1]
        h1, h2 = highs[p1], highs[p2]
        if abs(h1 - h2) / min(h1, h2) < 0.04 and (p2 - p1) <= 60:
            mid_troughs = [t for t in troughs if p1 < t < p2]
            if mid_troughs:
                t_mid = mid_troughs[0]
                neck_line = lows[t_mid]
                patterns.append({
                    "id": f"M頭_{dates[p2]}",
                    "name": "M頭 (Double Top)",
                    "type": "看空",
                    "date": dates[p2],
                    "skeleton_x": [dates[p1], dates[t_mid], dates[p2]],
                    "skeleton_y": [h1, neck_line, h2],
                    "skeleton_color": "#FF4500",
                    "neck_x": [dates[p1], dates[min(p2+10, n-1)]],
                    "neck_y": [neck_line, neck_line],
                    "neck_color": "#FF4500",
                    "annotations": [{"x": dates[p2], "y": h2, "text": "M頭", "color": "#FF4500"}]
                })

    # 3. 頭肩底
    for i in range(len(troughs) - 2):
        t1, t2, t3 = troughs[i], troughs[i+1], troughs[i+2]
        l1, l2, l3 = lows[t1], lows[t2], lows[t3]
        if l2 < l1 and l2 < l3 and abs(l1 - l3) / min(l1, l3) < 0.06:
            mid_p1 = [p for p in peaks if t1 < p < t2]
            mid_p2 = [p for p in peaks if t2 < p < t3]
            if mid_p1 and mid_p2:
                p1, p2 = mid_p1[0], mid_p2[0]
                patterns.append({
                    "id": f"頭肩底_{dates[t3]}",
                    "name": "頭肩底 (Head & Shoulders)",
                    "type": "看多",
                    "date": dates[t3],
                    "skeleton_x": [dates[t1], dates[p1], dates[t2], dates[p2], dates[t3]],
                    "skeleton_y": [l1, highs[p1], l2, highs[p2], l3],
                    "skeleton_color": "#00FFFF",
                    "neck_x": [dates[p1], dates[p2]],
                    "neck_y": [highs[p1], highs[p2]],
                    "neck_color": "#1E90FF",
                    "annotations": [{"x": dates[t2], "y": l2, "text": "頭肩底", "color": "#00FFFF"}]
                })

    # 4. 頭肩頂
    for i in range(len(peaks) - 2):
        p1, p2, p3 = peaks[i], peaks[i+1], peaks[i+2]
        h1, h2, h3 = highs[p1], highs[p2], highs[p3]
        if h2 > h1 and h2 > h3 and abs(h1 - h3) / min(h1, h3) < 0.06:
            mid_t1 = [t for t in troughs if p1 < t < p2]
            mid_t2 = [t for t in troughs if p2 < t < p3]
            if mid_t1 and mid_t2:
                t1_idx, t2_idx = mid_t1[0], mid_t2[0]
                patterns.append({
                    "id": f"頭肩頂_{dates[p3]}",
                    "name": "頭肩頂 (Head & Shoulders Top)",
                    "type": "看空",
                    "date": dates[p3],
                    "skeleton_x": [dates[p1], dates[t1_idx], dates[p2], dates[t2_idx], dates[p3]],
                    "skeleton_y": [h1, lows[t1_idx], h2, lows[t2_idx], h3],
                    "skeleton_color": "#FF1493",
                    "neck_x": [dates[t1_idx], dates[t2_idx]],
                    "neck_y": [lows[t1_idx], lows[t2_idx]],
                    "neck_color": "#FF4500",
                    "annotations": [{"x": dates[p2], "y": h2, "text": "頭肩頂", "color": "#FF1493"}]
                })

    return sorted(patterns, key=lambda x: x["date"], reverse=True)

# 側邊欄設定
st.sidebar.markdown("### 標的查詢")
stock_id = st.sidebar.text_input("台股代碼", value="2330").strip()

st.sidebar.markdown("---")
st.sidebar.markdown("### 時間區間")

curr_year = date.today().year
year_options = list(range(curr_year, 2009, -1))
month_options = list(range(1, 13))

# 開始日期選擇器
st.sidebar.markdown("**開始日期**")
col_s_yr, col_s_mo, col_s_dy = st.sidebar.columns(
