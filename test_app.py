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
            if mid_p1 and mid_p2:
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

# --- 開始日期選擇器 ---
st.sidebar.markdown("**開始日期**")
col_s_yr, col_s_mo, col_s_dy = st.sidebar.columns([3, 2, 2])
default_start_year = curr_year - 2
s_year = col_s_yr.selectbox("年", year_options, index=year_options.index(default_start_year), key="s_yr", label_visibility="collapsed")
s_month = col_s_mo.selectbox("月", month_options, index=date.today().month - 1, key="s_mo", label_visibility="collapsed")

max_s_day = calendar.monthrange(s_year, s_month)[1]
s_day = col_s_dy.selectbox("日", list(range(1, max_s_day + 1)), index=min(date.today().day, max_s_day) - 1, key="s_dy", label_visibility="collapsed")
start_date_input = date(s_year, s_month, s_day)

# --- 結束日期選擇器 ---
st.sidebar.markdown("**結束日期**")
col_e_yr, col_e_mo, col_e_dy = st.sidebar.columns([3, 2, 2])
e_year = col_e_yr.selectbox("年", year_options, index=0, key="e_yr", label_visibility="collapsed")
e_month = col_e_mo.selectbox("月", month_options, index=date.today().month - 1, key="e_mo", label_visibility="collapsed")

max_e_day = calendar.monthrange(e_year, e_month)[1]
e_day = col_e_dy.selectbox("日", list(range(1, max_e_day + 1)), index=min(date.today().day, max_e_day) - 1, key="e_dy", label_visibility="collapsed")
end_date_input = date(e_year, e_month, e_day)

st.sidebar.markdown("---")
st.sidebar.markdown("### 技術均線 (MA)")
col_ma1, col_ma2 = st.sidebar.columns(2)
ma1_val = col_ma1.number_input("MA 1", min_value=1, max_value=240, value=5)
ma2_val = col_ma2.number_input("MA 2", min_value=1, max_value=240, value=10)
col_ma3, col_ma4 = st.sidebar.columns(2)
ma3_val = col_ma3.number_input("MA 3", min_value=1, max_value=240, value=20)
ma4_val = col_ma4.number_input("MA 4", min_value=1, max_value=240, value=60)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("開始量化分析"):
    if start_date_input >= end_date_input:
        st.error("「開始日期」必須早於「結束日期」！")
    else:
        with st.spinner("正在加載歷史數據並繪製型態..."):
            try:
                ticker = f"{stock_id}.TW"
                start_str = start_date_input.strftime("%Y-%m-%d")
                end_str = end_date_input.strftime("%Y-%m-%d")

                df = yf.download(ticker, start=start_str, end=end_str)
                if df.empty:
                    df = yf.download(f"{stock_id}.TWO", start=start_str, end=end_str)

                if df.empty:
                    st.error("查無數據，請確認股票代碼！")
                    st.session_state.data_loaded = False
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    df.index = df.index.strftime('%Y-%m-%d')
                    st.session_state.df = df
                    st.session_state.company_name = get_taiwan_stock_name(stock_id)
                    st.session_state.detected_patterns = detect_patterns(df)
                    st.session_state.data_loaded = True

            except Exception as e:
                st.error(f"資料讀取失敗：{e}")
                st.session_state.data_loaded = False

# 主畫面渲染
if st.session_state.data_loaded:
    df = st.session_state.df.copy()
    company_name = st.session_state.company_name
    detected_patterns = st.session_state.detected_patterns

    # 計算均線
    df[f'MA_{ma1_val}'] = df['Close'].rolling(window=ma1_val).mean()
    df[f'MA_{ma2_val}'] = df['Close'].rolling(window=ma2_val).mean()
    df[f'MA_{ma3_val}'] = df['Close'].rolling(window=ma3_val).mean()
    df[f'MA_{ma4_val}'] = df['Close'].rolling(window=ma4_val).mean()

    # 數據指標卡片
    latest_close = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_close
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100 if prev_close > 0 else 0
    latest_vol = int(df["Volume"].iloc[-1]) // 1000

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{company_name} 最新價", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("前日收盤價", f"${prev_close:.2f}")
    col3.metric("最新成交量", f"{latest_vol:,} 張")
    col4.metric("區間最高價", f"${df['High'].max():.2f}")

    # 型態控制區塊
    st.markdown("---")
    st.markdown("#### AI 幾何型態疊加控制")

    pattern_options = [
        f"{p['date']} {p['name']} [{p['type']} {'📈' if p['type'] == '看多' else '📉'}]" 
        for p in detected_patterns
    ]

    if "selected_patterns" not in st.session_state:
        st.session_state.selected_patterns = []

    col_b1, col_b2, _ = st.columns([1.2, 1.2, 3.6])
    with col_b1:
        if st.button("全選標註"):
            st.session_state.selected_patterns = pattern_options
    with col_b2:
        if st.button("清爽模式"):
            st.session_state.selected_patterns = []

    selected_options = st.multiselect(
        "選擇要繪製在圖表上的幾何型態：",
        options=pattern_options,
        key="selected_patterns"
    )

    # 準備最新一筆數據作為預設固定顯示資訊
    df['Prev_Close'] = df['Close'].shift(1)
    df['Change'] = df['Close'] - df['Prev_Close']
    df['Pct_Change'] = (df['Change'] / df['Prev_Close']) * 100
    weekday_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}

    latest_row = df.iloc[-1]
    latest_dt = datetime.strptime(df.index[-1], '%Y-%m-%d')
    latest_weekday = weekday_map[latest_dt.weekday()]
    latest_color = "#FF4500" if latest_row['Change'] >= 0 else "#00FF7F"
    latest_sign = "+" if latest_row['Change'] >= 0 else ""

    fixed_info_text = (
        f"<b>{df.index[-1].replace('-','/')} {latest_weekday}</b><br>"
        f"開盤：<span style='color:{latest_color}'>{latest_row['Open']:.2f}</span><br>"
        f"最高：<span style='color:{latest_color}'>{latest_row['High']:.2f}</span><br>"
        f"最低：<span style='color:{latest_color}'>{latest_row['Low']:.2f}</span><br>"
        f"收盤：<span style='color:{latest_color}'>{latest_row['Close']:.2f}</span><br>"
        f"漲跌額：<span style='color:{latest_color}'>{latest_sign}{latest_row['Change']:.2f}</span><br>"
        f"漲跌幅：<span style='color:{latest_color}'>{latest_sign}{latest_row['Pct_Change']:.2f}%</span><br>"
        f"成交量：{int(latest_row['Volume'] // 1000):,} 張"
    )

    # Plotly 繪圖：強行共用 X 軸 (shared_xaxes=True)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.72, 0.28])

    # K線（關閉 hoverinfo="all" 改為 hoverinfo="x" 以配合純縱向十字線）
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#FF4500', decreasing_line_color='#00FF7F', name="K線",
        hoverinfo="x"
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma1_val}'], mode='lines', name=f'{ma1_val}MA', line=dict(color='#FFD700', width=1.2), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma2_val}'], mode='lines', name=f'{ma2_val}MA', line=dict(color='#00FFFF', width=1.2), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma3_val}'], mode='lines', name=f'{ma3_val}MA', line=dict(color='#FF00FF', width=1.5), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma4_val}'], mode='lines', name=f'{ma4_val}MA', line=dict(color='#1E90FF', width=1.5), hoverinfo='skip'), row=1, col=1)

    # 繪製選取的幾何型態
    patterns_to_draw = [
        p for p, opt_str in zip(detected_patterns, pattern_options) 
        if opt_str in selected_options
    ]
    for p in patterns_to_draw:
        if p["skeleton_x"]:
            fig.add_trace(go.Scatter(
                x=p["skeleton_x"], y=p["skeleton_y"], mode='lines+markers',
                name=f"{p['name']}", line=dict(color=p["skeleton_color"], width=2.5),
                marker=dict(size=6, color=p["skeleton_color"]), hoverinfo='skip'
            ), row=1, col=1)

        if p["neck_x"]:
            fig.add_trace(go.Scatter(
                x=p["neck_x"], y=p["neck_y"], mode='lines',
                name=f"{p['name']} 頸線", line=dict(color=p["neck_color"], width=1.8, dash="dash"),
                hoverinfo='skip'
            ), row=1, col=1)

        for ann in p.get("annotations", []):
            fig.add_annotation(
                x=ann["x"], y=ann["y"], text=ann["text"],
                showarrow=True, arrowhead=2, arrowcolor=ann["color"],
                font=dict(color="#FFFFFF", size=11), bgcolor=ann["color"], row=1, col=1
            )

    # 成交量
    colors = ['#FF4500' if c >= o else '#00FF7F' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'] / 1000, name="成交量(張)", marker_color=colors, hoverinfo='x'), row=2, col=1)

    # 💡 核心改動 1：使用獨立 Annotation 將資訊框「完美固定」在左上角 (xref="paper", yref="paper")
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.01, y=0.98,  # 左上角相對位置
        text=fixed_info_text,
        showarrow=False,
        align="left",
        font=dict(size=12, color="#F0F6FC"),
        bgcolor="rgba(22, 27, 34, 0.85)",
        bordercolor="#30363D",
        borderwidth=1,
        borderpad=8
    )

    # 版面配置
    fig.update_layout(
        title=f"<b>{company_name} ({stock_id}) 全功能技術分析圖</b>",
        title_font=dict(size=18, color="#F0F6FC"),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor="#161B22",
        plot_bgcolor="#0D1117",
        height=720,
        hovermode="x",
        margin=dict(r=20, t=50, l=20, b=80),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="left", x=0, font=dict(color="#C9D1D9")),
        dragmode="pan"
    )

    # 💡 核心改動 2：強制設定雙 X 軸連動與縱向貫穿線
    fig.update_xaxes(
        type='category', 
        tickangle=-45, 
        nticks=12,
        showgrid=True, 
        gridcolor="#21262D",
        showspikes=True, 
        spikemode='across+marker',  # 貫穿全圖
        spikesnap='cursor',
        spikethickness=1, 
        spikecolor='#8B949E', 
        spikedash='dash',
        fixedrange=False
    )

    fig.update_yaxes(
        side="right", title="股價 (TWD)",
        showgrid=True, gridcolor="#21262D",
        showspikes=True, spikemode='across', spikethickness=1, spikecolor='#8B949E', spikedash='dash',
        autorange=True, fixedrange=False, row=1, col=1
    )

    fig.update_yaxes(
        side="right", title="成交量 (張)",
        showgrid=True, gridcolor="#21262D",
        showspikes=True, spikemode='across', spikethickness=1, spikecolor='#8B949E', spikedash='dash',
        autorange=True, fixedrange=False, row=2, col=1
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'scrollZoom': True,
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['select2d', 'lasso2d']
        }
    )
else:
    st.info("請在左側側邊欄輸入股票代碼與區間，點擊「開始量化分析」按鈕。")
