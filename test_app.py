# 型態控制區塊
    st.markdown("---")
    st.markdown("#### AI 幾何型態疊加控制")

    # 1. 在選單文字後方加入多空走勢與 Emoji 標示
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

    # 2. 匹配選取的型態（使用列表比對確保精準繪製）
    patterns_to_draw = [
        p for p, opt_str in zip(detected_patterns, pattern_options) 
        if opt_str in selected_options
    ]
