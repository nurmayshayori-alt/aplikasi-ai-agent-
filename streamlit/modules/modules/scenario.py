import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes):
    sample_fc = pd.DataFrame({
        "Category": ["Product Revenue", "Service Income", "Direct Labor", "Raw Materials", "Marketing Opex"],
        "Base Forecast": [250000000, 90000000, 75000000, 85000000, 30000000]
    })

    with st.sidebar:
        uploaded_fc = st.file_uploader(
            "📂 Upload File Forecast (.xlsx / .csv)",
            type=["xlsx", "xls", "csv"],
            key="upload_fc"
        )
        st.download_button(
            label="📥 Contoh Excel Forecast",
            data=to_excel_bytes(sample_fc, "Forecast"),
            file_name="APRIYO_Template_Forecast.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        custom_shock = st.slider("🎛️ Simulasi What-If (%)", -50, 50, 0, 5)
        scenario_prompt = st.text_area("📝 Asumsi Skenario:", placeholder="Misal: Pendapatan turun 10%, biaya naik 5%", height=80)

    st.markdown("""
<div class="hero-banner">
<span class="hero-badge">APRIYO • PREDICTIVE FP&A & WHAT-IF SIMULATOR</span>
<h1>Scenario Planning & Strategic Copilot</h1>
<p>Simulasi proyeksi multi-skenario (Optimistic, Pessimistic, Worst Case, & Custom Shock) secara instan.</p>
</div>
""", unsafe_allow_html=True)

    if uploaded_fc is not None:
        raw_fc = read_any_tabular_file(uploaded_fc)
        df_fc = smart_column_mapper(
            raw_fc,
            {
                "Category": ["cat", "kat", "akun", "pos", "nama", "item"],
                "Base Forecast": ["base", "fore", "proyeksi", "nilai", "amount", "budget", "nominal"]
            },
            key_prefix="fc"
        )

        df_fc["Base Forecast"] = pd.to_numeric(df_fc["Base Forecast"], errors="coerce").fillna(0)
        np.random.seed(42)
        df_fc["Optimistic"] = df_fc["Base Forecast"] * np.random.uniform(1.10, 1.25, len(df_fc))
        df_fc["Pessimistic"] = df_fc["Base Forecast"] * np.random.uniform(0.75, 0.90, len(df_fc))
        df_fc["Worst Case"] = df_fc["Base Forecast"] * np.random.uniform(0.55, 0.70, len(df_fc))
        custom_col = f"Custom ({custom_shock:+d}%)"
        df_fc[custom_col] = df_fc["Base Forecast"] * (1 + custom_shock / 100.0)

        st.session_state["last_module_name"] = "Scenario Planning Forecast"
        st.session_state["last_module_df"] = df_fc

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📌 Base Forecast", f"{df_fc['Base Forecast'].sum():,.0f}", f"{len(df_fc)} Kategori")
        k2.metric("🌟 Optimistic", f"{df_fc['Optimistic'].sum():,.0f}", delta="+10% s/d +25%")
        k3.metric("🚨 Worst Case", f"{df_fc['Worst Case'].sum():,.0f}", delta="-30% s/d -45%", delta_color="inverse")
        k4.metric(f"🎛️ {custom_col}", f"{df_fc[custom_col].sum():,.0f}", delta=f"{custom_shock:+d}% Simulasi")

        t1, t2, t3 = st.tabs(["✨ Grafik Proyeksi", "📋 Tabel & Export", "🤖 AI Strategic Copilot"])

        with t1:
            fig_fc = go.Figure(data=[
                go.Bar(name="Base Forecast", x=df_fc["Category"], y=df_fc["Base Forecast"], marker=dict(color="#4f46e5", cornerradius=6)),
                go.Bar(name="Optimistic", x=df_fc["Category"], y=df_fc["Optimistic"], marker=dict(color="#10b981", cornerradius=6)),
                go.Bar(name="Pessimistic", x=df_fc["Category"], y=df_fc["Pessimistic"], marker=dict(color="#f59e0b", cornerradius=6)),
                go.Bar(name="Worst Case", x=df_fc["Category"], y=df_fc["Worst Case"], marker=dict(color="#e11d48", cornerradius=6)),
                go.Scatter(name=custom_col, x=df_fc["Category"], y=df_fc[custom_col], mode="lines+markers", line=dict(color="#0f172a", width=3, dash="dash"))
            ])
            fig_fc.update_layout(title="Simulasi Proyeksi Multi-Skenario", barmode="group", template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=380)
            st.plotly_chart(fig_fc, use_container_width=True)

        with t2:
            st.download_button("💾 Export Excel Forecast", data=to_excel_bytes(df_fc, "Forecast"), file_name="APRIYO_Forecast.xlsx")
            st.dataframe(df_fc.style.format({"Base Forecast": "{:,.2f}", "Optimistic": "{:,.2f}", "Pessimistic": "{:,.2f}", "Worst Case": "{:,.2f}", custom_col: "{:,.2f}"}), use_container_width=True)

        with t3:
            if st.button("🚀 Generate Strategi AI", type="primary"):
                with st.spinner("Menyusun strategi..."):
                    res_fc = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are an AI Financial Copilot specializing in scenario planning. Respond in Indonesian."},
                            {"role": "user", "content": f"Data:\n{df_fc.to_string(index=False)}\nAsumsi: {scenario_prompt}\nShock: {custom_shock:+d}%"}
                        ],
                        model=selected_model
                    )
                    st.session_state["fc_ai_summary"] = res_fc.choices[0].message.content
                    st.session_state["last_module_ai"] = st.session_state["fc_ai_summary"]
            if "fc_ai_summary" in st.session_state:
                st.markdown(st.session_state["fc_ai_summary"])
    else:
        st.markdown("""
<div class="empty-state-box">
<h3 style="color: #0f172a; margin-bottom: 8px;">📂 Unggah File Forecast (.xlsx atau .csv)</h3>
<p style="color: #475569; font-size: 14.5px; max-width: 560px; margin: 0 auto;">
Unggah tabel proyeksi dengan kolom nama akun/kategori dan nilai dasar proyeksi (nama kolom bebas).
</p>
</div>
""", unsafe_allow_html=True)
