import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import twstock
from datetime import datetime, date, timedelta
from scipy.signal import find_peaks

# 1. 網頁頁面設定
st.set_page_config(page_title="AI 台股量化分析看板", layout="wide")
st.title("📈 AI 智理財：全時間區間歷史 K 線與幾何型態掃描系統")
st.write("輸入台股代碼與自訂日期區間，AI 演算法將自動掃描經典型態，可手動選擇開啟型態標註。")

# 初始化 Session State
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "df" not in st.session_state:
    st.session_state.df = None
if "detected_patterns" not in st.session_state:
    st.session_state.detected_patterns = []
if "company_name" not in st.session_state:
    st.session_state.company_name = ""

# 2. 自動抓取中文名稱的函式
def get_taiwan_stock_name(stock_id):
    try:
        if stock_id in twstock.codes:
            return twstock.codes[stock_id].name
    except Exception:
        pass
    return f"股票 {stock_id}"

# 3. K 線與幾何型態全域自動識別
def detect_patterns(df):
    patterns = []
    prices = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    opens = df['Open'].values
    dates = df.index.tolist()
    n = len(prices)

    if n < 20:
        return patterns

    peaks, _ = find_peaks(highs, distance=5)
    troughs, _ = find_peaks(-lows, distance=5)

    # 1. W底 (Double Bottom)
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
                    "detail": f"日期: {dates[t1]} ~ {dates[t2]} | 第一底 ${l1:.1f}, 第二底 ${l2:.1f}, 頸線 ${neck_line:.1f}",
                    "skeleton_x": [dates[t1], dates[p_mid], dates[t2]],
                    "skeleton_y": [l1, neck_line, l2],
                    "skeleton_color": "#00FF7F",
                    "neck_x": [dates[t1], dates[min(t2+10, n-1)]],
                    "neck_y": [neck_line, neck_line],
                    "neck_color": "#1E90FF",
                    "annotations": [{"x": dates[t2], "y": l2, "text": "W底", "color": "#00FF7F"}]
                })

    # 2. M頭 (Double Top)
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
                    "detail": f"日期: {dates[p1]} ~ {dates[p2]} | 第一頂 ${h1:.1f}, 第二頂 ${h2:.1f}, 頸線 ${neck_line:.1f}",
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
                    "detail": f"日期: {dates[t1]} ~ {dates[t3]} | 左肩 ${l1:.1f}, 頭部 ${l2:.1f}, 右肩 ${l3:.1f}",
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
                    "detail": f"日期: {dates[p1]} ~ {dates[p3]} | 左肩 ${h1:.1f}, 頭部 ${h2:.1f}, 右肩 ${h3:.1f}",
                    "skeleton_x": [dates[p1], dates[t1_idx], dates[p2], dates[t2_idx], dates[p3]],
                    "skeleton_y": [h1, lows[t1_idx], h2, lows[t2_idx], h3],
                    "skeleton_color": "#FF1493",
                    "neck_x": [dates[t1_idx], dates[t2_idx]],
                    "neck_y": [lows[t1_idx], lows[t2_idx]],
                    "neck_color": "#FF4500",
                    "annotations": [{"x": dates[p2], "y": h2, "text": "頭肩頂", "color": "#FF1493"}]
                })

    patterns = sorted(patterns, key=lambda x: x["date"], reverse=True)
    return patterns

# 4. 側邊欄輸入與設定
st.sidebar.header("🔍 股票查詢")
stock_id = st.sidebar.text_input("請輸入台股代碼：", value="2330").strip()

st.sidebar.markdown("---")
st.sidebar.header("📅 自訂歷史分析區間")
default_start = date.today() - timedelta(days=365*2)
start_date_input = st.sidebar.date_input("開始日期", value=default_start, min_value=date(2010, 1, 1), max_value=date.today())
end_date_input = st.sidebar.date_input("結束日期", value=date.today(), min_value=date(2010, 1, 1), max_value=date.today())

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 均線參數 (MA)")
ma1_val = st.sidebar.number_input("均線 1 (日)", min_value=1, max_value=240, value=5)
ma2_val = st.sidebar.number_input("均線 2 (日)", min_value=1, max_value=240, value=10)
ma3_val = st.sidebar.number_input("均線 3 (日)", min_value=1, max_value=240, value=20)
ma4_val = st.sidebar.number_input("均線 4 (日)", min_value=1, max_value=240, value=60)

# 觸發抓取資料的按鈕處理邏輯
if st.sidebar.button("開始分析"):
    if start_date_input >= end_date_input:
        st.error("「開始日期」必須早於「結束日期」！")
    else:
        with st.spinner("正在讀取歷史數據並分析型態..."):
            try:
                ticker = f"{stock_id}.TW"
                start_str = start_date_input.strftime("%Y-%m-%d")
                end_str = end_date_input.strftime("%Y-%m-%d")

                df = yf.download(ticker, start=start_str, end=end_str)
                if df.empty:
                    df = yf.download(f"{stock_id}.TWO", start=start_str, end=end_str)

                if df.empty:
                    st.error("找不到數據，請確認代碼與日期！")
                    st.session_state.data_loaded = False
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    df.index = df.index.strftime('%Y-%m-%d')
                    
                    # 保存進 session_state
                    st.session_state.df = df
                    st.session_state.company_name = get_taiwan_stock_name(stock_id)
                    st.session_state.detected_patterns = detect_patterns(df)
                    st.session_state.data_loaded = True

            except Exception as e:
                st.error(f"數據分析失敗：{e}")
                st.session_state.data_loaded = False

# 5. 主畫面繪製邏輯（只要 state 中有資料就會持續渲染）
if st.session_state.data_loaded:
    df = st.session_state.df.copy()
    company_name = st.session_state.company_name
    detected_patterns = st.session_state.detected_patterns

    # 動態計算均線
    df[f'MA_{ma1_val}'] = df['Close'].rolling(window=ma1_val).mean()
    df[f'MA_{ma2_val}'] = df['Close'].rolling(window=ma2_val).mean()
    df[f'MA_{ma3_val}'] = df['Close'].rolling(window=ma3_val).mean()
    df[f'MA_{ma4_val}'] = df['Close'].rolling(window=ma4_val).mean()

    # 核心指標卡片
    st.subheader(f"📊 {company_name} ({stock_id}) 核心指標")
    latest_close = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_close
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100 if prev_close > 0 else 0
    latest_vol = int(df["Volume"].iloc[-1]) // 1000

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新收盤價", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("前日收盤價", f"${prev_close:.2f}")
    col3.metric("成交量 (張)", f"{latest_vol:,}")
    col4.metric("區間最高價", f"${df['High'].max():.2f}")

    # 下拉選單與控制控制項
    st.markdown("---")
    col_p1, col_p2 = st.columns([1.5, 2.5])
    with col_p1:
        st.subheader("🔍 AI 型態控制選單")
        pattern_options = ["不顯示型態 (清爽模式)", "顯示全域所有型態"] + [f"{p['date']} {p['name']}" for p in detected_patterns]
        selected_option = st.selectbox("請選擇要在圖表顯示的型態：", pattern_options)
    
    with col_p2:
        if detected_patterns:
            st.info(f"💡 區間內共掃描出 **{len(detected_patterns)}** 個關鍵幾何型態。選取左側項目即可在圖表畫線標註。")
        else:
            st.warning("該區間內未辨識出明顯幾何型態。")

    # Hover 文字處理
    df['Prev_Close'] = df['Close'].shift(1)
    df['Change'] = df['Close'] - df['Prev_Close']
    df['Pct_Change'] = (df['Change'] / df['Prev_Close']) * 100
    weekday_map = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}

    hover_texts = []
    for dt_str, row in df.iterrows():
        dt = datetime.strptime(dt_str, '%Y-%m-%d')
        weekday_str = weekday_map[dt.weekday()]
        change_val = row['Change'] if pd.notnull(row['Change']) else 0.0
        pct_val = row['Pct_Change'] if pd.notnull(row['Pct_Change']) else 0.0
        vol_zhang = int(row['Volume'] // 1000)
        
        color = "#FF4500" if change_val >= 0 else "#00FF7F"
        sign = "+" if change_val >= 0 else ""

        text = (
            f"<b>{dt_str.replace('-','/')} {weekday_str}</b><br>"
            f"開盤：<span style='color:{color}'>{row['Open']:.3f}</span><br>"
            f"最高：<span style='color:{color}'>{row['High']:.3f}</span><br>"
            f"最低：<span style='color:{color}'>{row['Low']:.3f}</span><br>"
            f"收盤：<span style='color:{color}'>{row['Close']:.3f}</span><br>"
            f"漲跌額：<span style='color:{color}'>{sign}{change_val:.3f}</span><br>"
            f"漲跌幅：<span style='color:{color}'>{sign}{pct_val:.2f}%</span><br>"
            f"成交量(張)：{vol_zhang:,}"
        )
        hover_texts.append(text)

    # 繪製圖表
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])

    # K線
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='red', decreasing_line_color='green', name="K線",
        text=hover_texts, hoverinfo="text"
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma1_val}'], mode='lines', name=f'{ma1_val}MA', line=dict(color='orange', width=1), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma2_val}'], mode='lines', name=f'{ma2_val}MA', line=dict(color='cyan', width=1), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma3_val}'], mode='lines', name=f'{ma3_val}MA', line=dict(color='yellow', width=1.2), hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma4_val}'], mode='lines', name=f'{ma4_val}MA', line=dict(color='magenta', width=1.2), hoverinfo='skip'), row=1, col=1)

    # 動態繪製型態
    patterns_to_draw = []
    if selected_option == "顯示全域所有型態":
        patterns_to_draw = detected_patterns
    elif selected_option != "不顯示型態 (清爽模式)":
        patterns_to_draw = [p for p in detected_patterns if f"{p['date']} {p['name']}" == selected_option]

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
                font=dict(color="#FFFFFF", size=10), bgcolor=ann["color"], row=1, col=1
            )

    # 成交量
    colors = ['red' if c >= o else 'green' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'] / 1000, name="成交量(張)", marker_color=colors, hoverinfo='skip'), row=2, col=1)

    # Layout 設定
    fig.update_layout(
        title=f"{company_name} ({stock_id}) 技術走勢圖",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        height=750,
        hovermode="x",
        hoverlabel=dict(bgcolor="rgba(25, 25, 25, 0.9)", font_size=12, font_color="#FFFFFF", align="left"),
        margin=dict(r=60, t=50, l=20, b=100),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0)
    )

    fig.update_xaxes(type='category', tickangle=-45, nticks=12, showspikes=True, spikemode='across', spikethickness=1, spikecolor='#888888', spikedash='dash')
    fig.update_yaxes(side="right", title="股價 (TWD)", showspikes=True, spikemode='across', spikethickness=1, spikecolor='#888888', spikedash='dash', row=1, col=1)
    fig.update_yaxes(side="right", title="成交量 (張)", showspikes=True, spikemode='across', spikethickness=1, spikecolor='#888888', spikedash='dash', row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 請在左側輸入股票代碼與時間區間，並點擊「開始分析」即可產生技術分析圖表。")
