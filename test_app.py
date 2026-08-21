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
st.title("📈 AI 智理財：台股多重 K 線與幾何型態繪圖系統")
st.write("輸入台股股票代碼，可自由切換**自訂日期區間**，即時計算動態均線、價量結構與 **9 大 K 線/幾何型態繪圖標註**。")

# 2. 自動抓取中文名稱的函式
def get_taiwan_stock_name(stock_id):
    try:
        if stock_id in twstock.codes:
            return twstock.codes[stock_id].name
    except Exception:
        pass
    return f"股票 {stock_id}"

# 3. K 線與幾何型態自動識別 (含 9 大進階型態)
def detect_patterns(df):
    patterns = []
    prices = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    opens = df['Open'].values
    dates = df.index.tolist()
    n = len(prices)

    if n < 30:
        return patterns

    # 尋找局部高點與低點
    peaks, _ = find_peaks(highs, distance=7)
    troughs, _ = find_peaks(-lows, distance=7)
    latest_close = prices[-1]

    # ----------------------------------------------------
    # 1. 頭肩底 (Head & Shoulders Bottom) - 看多
    # ----------------------------------------------------
    if len(troughs) >= 3:
        t1, t2, t3 = troughs[-3], troughs[-2], troughs[-1]
        l1, l2, l3 = lows[t1], lows[t2], lows[t3]
        if l2 < l1 and l2 < l3 and abs(l1 - l3) / min(l1, l3) < 0.06:
            mid_p1 = [p for p in peaks if t1 < p < t2]
            mid_p2 = [p for p in peaks if t2 < p < t3]
            if mid_p1 and mid_p2:
                p1, p2 = mid_p1[0], mid_p2[0]
                h1, h2 = highs[p1], highs[p2]
                patterns.append({
                    "name": "頭肩底 (Head & Shoulders Bottom)",
                    "type": "看多",
                    "detail": f"左肩: ${l1:.1f}, 頭部: ${l2:.1f}, 右肩: ${l3:.1f}",
                    "skeleton_x": [dates[t1], dates[p1], dates[t2], dates[p2], dates[t3], dates[-1]],
                    "skeleton_y": [l1, h1, l2, h2, l3, latest_close],
                    "skeleton_color": "#00FFFF",
                    "neck_x": [dates[p1], dates[-1]],
                    "neck_y": [h1, h2 if p1==p2 else h1 + (h2-h1)*(n-1-p1)/(p2-p1)],
                    "neck_color": "#1E90FF",
                    "annotations": [
                        {"x": dates[t1], "y": l1, "text": "左肩", "color": "#00FFFF"},
                        {"x": dates[t2], "y": l2, "text": "頭部 (最低)", "color": "#00FFFF"},
                        {"x": dates[t3], "y": l3, "text": "右肩", "color": "#00FFFF"}
                    ]
                })

    # ----------------------------------------------------
    # 2. 頭肩頂 (Head & Shoulders Top) - 看空 (新增)
    # ----------------------------------------------------
    if len(peaks) >= 3:
        p1, p2, p3 = peaks[-3], peaks[-2], peaks[-1]
        h1, h2, h3 = highs[p1], highs[p2], highs[p3]
        if h2 > h1 and h2 > h3 and abs(h1 - h3) / min(h1, h3) < 0.06:
            mid_t1 = [t for t in troughs if p1 < t < p2]
            mid_t2 = [t for t in troughs if p2 < t < p3]
            if mid_t1 and mid_t2:
                t1_idx, t2_idx = mid_t1[0], mid_t2[0]
                l1_val, l2_val = lows[t1_idx], lows[t2_idx]
                patterns.append({
                    "name": "頭肩頂 (Head & Shoulders Top)",
                    "type": "看空",
                    "detail": f"左頭頂: ${h1:.1f}, 頭部最高: ${h2:.1f}, 右頭頂: ${h3:.1f}",
                    "skeleton_x": [dates[p1], dates[t1_idx], dates[p2], dates[t2_idx], dates[p3], dates[-1]],
                    "skeleton_y": [h1, l1_val, h2, l2_val, h3, latest_close],
                    "skeleton_color": "#FF1493",
                    "neck_x": [dates[t1_idx], dates[-1]],
                    "neck_y": [l1_val, l2_val],
                    "neck_color": "#FF4500",
                    "annotations": [
                        {"x": dates[p1], "y": h1, "text": "左肩", "color": "#FF1493"},
                        {"x": dates[p2], "y": h2, "text": "頭部 (最高)", "color": "#FF1493"},
                        {"x": dates[p3], "y": h3, "text": "右肩", "color": "#FF1493"}
                    ]
                })

    # ----------------------------------------------------
    # 3. W底 (Double Bottom) - 看多
    # ----------------------------------------------------
    if len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        l1, l2 = lows[t1], lows[t2]
        if abs(l1 - l2) / min(l1, l2) < 0.04:
            mid_peaks = [p for p in peaks if t1 < p < t2]
            if mid_peaks:
                p_mid = mid_peaks[0]
                neck_line = highs[p_mid]
                status = "🟢 突破頸線" if latest_close > neck_line else "🟡 醞釀中"
                patterns.append({
                    "name": "W底 (Double Bottom)",
                    "type": "看多",
                    "detail": f"底1: ${l1:.1f}, 底2: ${l2:.1f}, 頸線: ${neck_line:.1f} | 狀態: {status}",
                    "skeleton_x": [dates[t1], dates[p_mid], dates[t2], dates[-1]],
                    "skeleton_y": [l1, neck_line, l2, latest_close],
                    "skeleton_color": "#00FF7F",
                    "neck_x": [dates[t1], dates[-1]],
                    "neck_y": [neck_line, neck_line],
                    "neck_color": "#1E90FF",
                    "annotations": [
                        {"x": dates[t1], "y": l1, "text": "第一底", "color": "#00FF7F"},
                        {"x": dates[t2], "y": l2, "text": "第二底", "color": "#00FF7F"},
                        {"x": dates[p_mid], "y": neck_line, "text": f"頸線 ${neck_line:.1f}", "color": "#1E90FF"}
                    ]
                })

    # ----------------------------------------------------
    # 4. M頭 (Double Top) - 看空
    # ----------------------------------------------------
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        h1, h2 = highs[p1], highs[p2]
        if abs(h1 - h2) / min(h1, h2) < 0.04:
            mid_troughs = [t for t in troughs if p1 < t < p2]
            if mid_troughs:
                t_mid = mid_troughs[0]
                neck_line = lows[t_mid]
                status = "🔴 跌破頸線" if latest_close < neck_line else "🟡 醞釀中"
                patterns.append({
                    "name": "M頭 (Double Top)",
                    "type": "看空",
                    "detail": f"頂1: ${h1:.1f}, 頂2: ${h2:.1f}, 頸線: ${neck_line:.1f} | 狀態: {status}",
                    "skeleton_x": [dates[p1], dates[t_mid], dates[p2], dates[-1]],
                    "skeleton_y": [h1, neck_line, h2, latest_close],
                    "skeleton_color": "#FF4500",
                    "neck_x": [dates[p1], dates[-1]],
                    "neck_y": [neck_line, neck_line],
                    "neck_color": "#FF4500",
                    "annotations": [
                        {"x": dates[p1], "y": h1, "text": "第一頂", "color": "#FF4500"},
                        {"x": dates[p2], "y": h2, "text": "第二頂", "color": "#FF4500"},
                        {"x": dates[t_mid], "y": neck_line, "text": f"頸線 ${neck_line:.1f}", "color": "#FF4500"}
                    ]
                })

    # ----------------------------------------------------
    # 5. 三重底 (Triple Bottom) - 看多 (新增)
    # ----------------------------------------------------
    if len(troughs) >= 3:
        t1, t2, t3 = troughs[-3], troughs[-2], troughs[-1]
        l1, l2, l3 = lows[t1], lows[t2], lows[t3]
        max_l = max(l1, l2, l3)
        min_l = min(l1, l2, l3)
        if (max_l - min_l) / min_l < 0.03:
            patterns.append({
                "name": "三重底 (Triple Bottom)",
                "type": "強烈看多",
                "detail": f"三底均於 ${min_l:.1f} ~ ${max_l:.1f} 獲得強烈支撐",
                "skeleton_x": [dates[t1], dates[t2], dates[t3]],
                "skeleton_y": [l1, l2, l3],
                "skeleton_color": "#32CD32",
                "neck_x": [dates[t1], dates[-1]],
                "neck_y": [max_l, max_l],
                "neck_color": "#32CD32",
                "annotations": [
                    {"x": dates[t2], "y": l2, "text": "三重底築底成功", "color": "#32CD32"}
                ]
            })

    # ----------------------------------------------------
    # 6. 上升三角 (Ascending Triangle) - 看多 (新增)
    # ----------------------------------------------------
    if len(peaks) >= 2 and len(troughs) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        t1, t2 = troughs[-2], troughs[-1]
        if abs(highs[p1] - highs[p2]) / highs[p1] < 0.025 and lows[t2] > lows[t1] * 1.02:
            patterns.append({
                "name": "上升三角 (Ascending Triangle)",
                "type": "看多",
                "detail": f"高點平齊阻力: ${highs[p1]:.1f}, 低點持續墊高 (${lows[t1]:.1f} -> ${lows[t2]:.1f})",
                "skeleton_x": [dates[t1], dates[p1], dates[t2], dates[p2]],
                "skeleton_y": [lows[t1], highs[p1], lows[t2], highs[p2]],
                "skeleton_color": "#FFD700",
                "neck_x": [dates[p1], dates[-1]],
                "neck_y": [highs[p1], highs[p1]],
                "neck_color": "#FFD700",
                "annotations": [
                    {"x": dates[p2], "y": highs[p2], "text": "高點壓力牆", "color": "#FFD700"},
                    {"x": dates[t2], "y": lows[t2], "text": "低點墊高", "color": "#00FF7F"}
                ]
            })

    # ----------------------------------------------------
    # 7. 下降三角 (Descending Triangle) - 看空 (新增)
    # ----------------------------------------------------
    if len(peaks) >= 2 and len(troughs) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        t1, t2 = troughs[-2], troughs[-1]
        if abs(lows[t1] - lows[t2]) / lows[t1] < 0.025 and highs[p2] < highs[p1] * 0.98:
            patterns.append({
                "name": "下降三角 (Descending Triangle)",
                "type": "看空",
                "detail": f"低點水平支撐: ${lows[t1]:.1f}, 高點持續降低 (${highs[p1]:.1f} -> ${highs[p2]:.1f})",
                "skeleton_x": [dates[p1], dates[t1], dates[p2], dates[t2]],
                "skeleton_y": [highs[p1], lows[t1], highs[p2], lows[t2]],
                "skeleton_color": "#FF6347",
                "neck_x": [dates[t1], dates[-1]],
                "neck_y": [lows[t1], lows[t1]],
                "neck_color": "#FF6347",
                "annotations": [
                    {"x": dates[t2], "y": lows[t2], "text": "水平支撐線", "color": "#FF6347"},
                    {"x": dates[p2], "y": highs[p2], "text": "高點降低", "color": "#FF4500"}
                ]
            })

    # ----------------------------------------------------
    # 8. K線訊號：多頭吞噬 / 空頭吞噬 (新增)
    # ----------------------------------------------------
    for i in range(-5, -1):  # 掃描近幾天 K 線
        prev_o, prev_c = opens[i-1], prices[i-1]
        curr_o, curr_c = opens[i], prices[i]
        
        # 多頭吞噬：前一根黑K，這根紅K完全包覆前一根實體
        if prev_c < prev_o and curr_c > curr_o and curr_o <= prev_c and curr_c >= prev_o:
            patterns.append({
                "name": "多頭吞噬 (Bullish Engulfing)",
                "type": "看多 (K線訊號)",
                "detail": f"日期: {dates[i]}，長紅K完全包覆前一日黑K實體，為強烈止跌轉強訊號",
                "skeleton_x": [], "skeleton_y": [],
                "neck_x": [], "neck_y": [],
                "annotations": [
                    {"x": dates[i], "y": lows[i], "text": "多頭吞噬", "color": "#00FF7F"}
                ]
            })
            break

        # 空頭吞噬：前一根紅K，這根黑K完全包覆前一根實體
        elif prev_c > prev_o and curr_c < curr_o and curr_o >= prev_c and curr_c <= prev_o:
            patterns.append({
                "name": "空頭吞噬 (Bearish Engulfing)",
                "type": "看空 (K線訊號)",
                "detail": f"日期: {dates[i]}，長黑K完全包覆前一日紅K實體，為強烈見頂轉弱訊號",
                "skeleton_x": [], "skeleton_y": [],
                "neck_x": [], "neck_y": [],
                "annotations": [
                    {"x": dates[i], "y": highs[i], "text": "空頭吞噬", "color": "#FF4500"}
                ]
            })
            break

    # ----------------------------------------------------
    # 9. 箱型整理 (Box Range)
    # ----------------------------------------------------
    recent_30_high = max(highs[-30:])
    recent_30_low = min(lows[-30:])
    box_range = (recent_30_high - recent_30_low) / recent_30_low
    if box_range < 0.09:
        patterns.append({
            "name": "箱型整理 (Box)",
            "type": "中立",
            "detail": f"近 30 日於箱頂 ${recent_30_high:.1f} 與箱底 ${recent_30_low:.1f} 震盪整理",
            "skeleton_x": [],
            "skeleton_y": [],
            "neck_x": [dates[-30], dates[-1]],
            "neck_y": [recent_30_high, recent_30_high],
            "neck_color": "#FFD700",
            "annotations": [
                {"x": dates[-15], "y": recent_30_high, "text": f"箱頂 ${recent_30_high:.1f}", "color": "#FFD700"},
                {"x": dates[-15], "y": recent_30_low, "text": f"箱底 ${recent_30_low:.1f}", "color": "#FFD700"}
            ]
        })

    return patterns

# 4. 側邊欄輸入與設定
st.sidebar.header("🔍 股票查詢")
stock_id = st.sidebar.text_input("請輸入台股代碼 (例如 2330, 0050, 2603)：", value="2330").strip()
ticker = f"{stock_id}.TW"

st.sidebar.markdown("---")
st.sidebar.header("📅 自訂分析日期區間")
default_start = date.today() - timedelta(days=365)
start_date_input = st.sidebar.date_input("開始日期", value=default_start, min_value=date(2015, 1, 1), max_value=date.today())
end_date_input = st.sidebar.date_input("結束日期", value=date.today(), min_value=date(2015, 1, 1), max_value=date.today())

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 客製化均線參數 (MA)")
ma1_val = st.sidebar.number_input("均線 1 (日)", min_value=1, max_value=240, value=5, step=1)
ma2_val = st.sidebar.number_input("均線 2 (日)", min_value=1, max_value=240, value=10, step=1)
ma3_val = st.sidebar.number_input("均線 3 (日)", min_value=1, max_value=240, value=20, step=1)
ma4_val = st.sidebar.number_input("均線 4 (日)", min_value=1, max_value=240, value=60, step=1)

# 5. 數據抓取與顯示
if st.sidebar.button("開始分析"):
    if start_date_input >= end_date_input:
        st.error("「開始日期」必須早於「結束日期」，請重新選擇！")
    else:
        with st.spinner("正在讀取指定區間市場數據並進行 AI 型態掃描..."):
            try:
                company_name = get_taiwan_stock_name(stock_id)

                start_str = start_date_input.strftime("%Y-%m-%d")
                end_str = end_date_input.strftime("%Y-%m-%d")

                df = yf.download(ticker, start=start_str, end=end_str)

                if df.empty:
                    ticker_otc = f"{stock_id}.TWO"
                    df = yf.download(ticker_otc, start=start_str, end=end_str)

                if df.empty:
                    st.error("找不到該股票在指定日期區間的數據，請確認代碼與日期！")
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)

                    # 計算均線
                    df[f'MA_{ma1_val}'] = df['Close'].rolling(window=ma1_val).mean()
                    df[f'MA_{ma2_val}'] = df['Close'].rolling(window=ma2_val).mean()
                    df[f'MA_{ma3_val}'] = df['Close'].rolling(window=ma3_val).mean()
                    df[f'MA_{ma4_val}'] = df['Close'].rolling(window=ma4_val).mean()

                    # ---- 核心價量指標 ----
                    st.subheader(f"📊 {company_name} ({stock_id}) 核心價量指標 ({start_str} ~ {end_str})")
                    
                    latest_close = float(df["Close"].iloc[-1])
                    prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_close
                    price_change = latest_close - prev_close
                    pct_change = (price_change / prev_close) * 100 if prev_close > 0 else 0

                    latest_vol = int(df["Volume"].iloc[-1]) // 1000
                    prev_vol = int(df["Volume"].iloc[-2]) // 1000 if len(df) > 1 else latest_vol
                    vol_change = latest_vol - prev_vol
                    vol_pct_change = (vol_change / prev_vol * 100) if prev_vol > 0 else 0

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("最新收盤價", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
                    col2.metric("前一交易日收盤價", f"${prev_close:.2f}")
                    col3.metric("最新成交量 (張)", f"{latest_vol:,}", f"{vol_change:+,} 張 ({vol_pct_change:+.1f}%)")
                    col4.metric("區間最高價", f"${df['High'].max():.2f}")

                    # 日期轉換為字串
                    df.index = df.index.strftime('%Y-%m-%d')

                    # 型態識別
                    detected_patterns = detect_patterns(df)

                    # ---- 型態資訊提示區塊 ----
                    st.markdown("---")
                    st.subheader("🔍 AI 演算法：K 線與幾何型態掃描結果")
                    if detected_patterns:
                        for p in detected_patterns:
                            if "看多" in p["type"]:
                                st.success(f"**【{p['name']}】** ({p['type']}) — {p['detail']}")
                            elif "看空" in p["type"]:
                                st.error(f"**【{p['name']}】** ({p['type']}) — {p['detail']}")
                            else:
                                st.info(f"**【{p['name']}】** ({p['type']}) — {p['detail']}")
                    else:
                        st.warning("在此時間區間內未偵測到顯著的經典幾何或 K 線型態，當前處於一般趨勢整理中。")

                    # ---- 圖表繪製 ----
                    st.subheader(f"📈 {start_str} ~ {end_str} 歷史走勢與視覺化圖表標註")
                    
                    fig = make_subplots(
                        rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3]
                    )

                    # 1. 主圖：K線
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                        increasing_line_color='red', decreasing_line_color='green', name="K線"
                    ), row=1, col=1)

                    # 2. 主圖：均線
                    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma1_val}'], mode='lines', name=f'{ma1_val}日均線', line=dict(color='orange', width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma2_val}'], mode='lines', name=f'{ma2_val}日均線', line=dict(color='cyan', width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma3_val}'], mode='lines', name=f'{ma3_val}日均線', line=dict(color='yellow', width=1.2)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df[f'MA_{ma4_val}'], mode='lines', name=f'{ma4_val}日均線', line=dict(color='magenta', width=1.2)), row=1, col=1)

                    # 3. 型態骨架與頸線標註
                    for p in detected_patterns:
                        if p["skeleton_x"]:
                            fig.add_trace(go.Scatter(
                                x=p["skeleton_x"], 
                                y=p["skeleton_y"], 
                                mode='lines+markers',
                                name=f"{p['name']} 骨架",
                                line=dict(color=p["skeleton_color"], width=3),
                                marker=dict(size=7, color=p["skeleton_color"])
                            ), row=1, col=1)

                        if p["neck_x"]:
                            fig.add_trace(go.Scatter(
                                x=p["neck_x"], 
                                y=p["neck_y"], 
                                mode='lines',
                                name=f"{p['name']} 頸線",
                                line=dict(color=p["neck_color"], width=2, dash="dash")
                            ), row=1, col=1)

                        for ann in p.get("annotations", []):
                            fig.add_annotation(
                                x=ann["x"], y=ann["y"],
                                text=ann["text"],
                                showarrow=True,
                                arrowhead=2,
                                arrowsize=1.2,
                                arrowcolor=ann["color"],
                                font=dict(color="#FFFFFF", size=11, family="Arial Black"),
                                bgcolor=ann["color"],
                                bordercolor="#FFFFFF",
                                borderwidth=1,
                                row=1, col=1
                            )

                    # 4. 副圖：成交量
                    colors = ['red' if c >= o else 'green' for c, o in zip(df['Close'], df['Open'])]
                    fig.add_trace(go.Bar(
                        x=df.index, 
                        y=df['Volume'] / 1000, 
                        name="成交量(張)", 
                        marker_color=colors
                    ), row=2, col=1)

                    fig.update_layout(
                        title=f"{company_name} ({stock_id}) 技術指標與 K 線幾何型態標註圖",
                        yaxis_title="股價 (TWD)",
                        yaxis2_title="成交量 (張)",
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark",
                        height=720,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )

                    fig.update_xaxes(
                        type='category', 
                        tickangle=-45,
                        nticks=10
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"資料擷取或型態分析失敗：{e}")
