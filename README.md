# 📈 AI 智理財：量化技術走勢與型態掃描看板

本專案為基於 **Streamlit** 與 **Plotly** 開發的台股量化技術分析系統，結合 **SciPy 訊號處理演算法** 實現經典 K 線幾何型態（如 W底、M頭、頭肩底、頭肩頂）的自動識別與圖表動態標註，為投資決策提供視覺化與數據驅動的輔助工具。

---

## 📌 系統核心功能與技術實作

### 1. 互動式 UI 與客製化視覺
* **Streamlit 介面佈局**：運用 `st.set_page_config` 與自訂 **CSS 樣式**（包含深色模式主題、自訂 `stMetric` 與按鈕樣式）打造現代化儀表板。
* **數據指標卡片**：即時計算並顯示最新股價、漲跌幅、前日收盤價、最新成交量與區間最高價。

### 2. 金融數據整合與預處理
* **歷史數據抓取**：整合 `yfinance` API 自動處理 `.TW` (上市) 與 `.TWO` (上櫃) 股票資料。
* **中文名稱對應**：調用 `twstock` 模組自動匹配台股代碼對應之公司中文名稱。
* **多重指標計算**：利用 `pandas` 滾動視窗（`rolling`）動態計算 MA5、MA10、MA20、MA60 等技術均線與每日漲跌幅。

### 3. K 線幾何型態自動辨識演算法
* **極值點偵測**：運用 `scipy.signal.find_peaks` 演算法精準搜尋價格的波峰（Peaks）與波谷（Troughs）。
* **經典型態辨識邏輯**：
  * **W底 (Double Bottom) / M頭 (Double Top)**：辨識雙重谷值/峰值與中間頸線位置。
  * **頭肩底 (Head & Shoulders) / 頭肩頂**：檢測三連波峰/波谷之相對高低差與型態對稱性。
* **動態圖案疊加**：支援使用者彈性「全選標註」或開啟「清爽模式」，將幾何骨架與頸線延伸線動態繪製於圖表上。

### 4. 進階動態圖表 (Plotly Subplots)
* **雙圖動態連動**：使用 `plotly.subplots` 將上方 K 線與下方成交量圖共用同一 X 軸（`shared_xaxes=True`）。
* **十字準心連動**：設定 `spikemode='across'` 與 `spikesnap='cursor'`，讓垂直虛線跨圖表完全跟隨游標。
* **無級縮放與滾輪支援**：開啟 `scrollZoom` 與 `hovermode="x unified"`，實現滑鼠自由縮放與數據鎖定檢視。

---

## 🛠️ 開發環境與套件版本

* **Language**: Python 3.10+
* **Framework**: Streamlit
* **Data & Analytics**: Pandas, NumPy, SciPy, yfinance, twstock
* **Visualization**: Plotly
* **Version Control**: GitHub

---

## 🚀 快速開始 (Quick Start)

### 1. 安裝依賴套件
```bash
pip install streamlit yfinance pandas numpy plotly twstock scipy
