import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes):
    sample_cf = pd.DataFrame({
        "Bulan": ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "Mei 2026", "Jun 2026"],
        "Cash Inflow": [320000000, 290000000, 350000000, 310000000, 380000000, 410000000],
        "Cash Outflow": [280000000, 315000000, 300000000, 340000000, 330000000, 350000000]
    })

    with st.sidebar:
        uploaded_cf = st.file_uploader(
            "📂 Upload Data Arus Kas (.xlsx / .csv)",
            type=["xlsx", "xls", "csv"],
            key="upload_cf"
        )
        st.download_button(
            label="📥 Contoh Excel Cash Flow",
            data=to_excel_bytes(sample_cf, "CashFlow"),
            file_name="APRIYO_Template_CashFlow.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        initial_cash = st.number_input("🏦 Saldo Kas Awal (Rp)", min_value=0, value=500000000, step=10000000)

    st.markdown("""
<div class="hero-banner">
<span class="hero-badge">APRIYO • TREASURY & LIQUIDITY MANAGEMENT</span>
<h1>Cash Flow & Liquidity Monitor</h1>
<p>Pantau arus kas masuk-keluar, Net Cash Flow kumulatif, rata-rata Burn Rate, dan estimasi Cash Runway perusahaan.</p>
</div>
""", unsafe_allow_html=True)

    if uploaded_cf is not None:
        raw_cf = read_any_tabular_file(uploaded_cf)
        df_cf = smart_column_mapper(
            raw_cf,
            {
                "Periode": ["bul", "month", "tgl", "date", "per", "waktu"],
                "Cash Inflow": ["in", "masuk", "terima", "pendapatan", "rev", "debet"],
                "Cash Outflow": ["out", "keluar", "bayar", "biaya", "exp", "kredit"]
            },
            key_prefix="cf"
        )

        df_cf["Cash Inflow"] = pd.to_numeric(df_cf["Cash Inflow"], errors="coerce").fillna(0)
        df_cf["Cash Outflow"] = pd.to_numeric(df_cf["Cash Outflow"], errors="coerce").fillna(0)
        df_cf["Net Cash Flow"] = df_cf["Cash Inflow"] - df_cf["Cash Outflow"]
        df_cf["Saldo Kas Akhir"] = initial_cash + df_cf["Net Cash Flow"].cumsum()

        st.session_state["last_module_name"] = "Cash Flow & Liquidity Analysis"
        st.session_state["last_module_df"] = df_cf

        tot_in = df_cf["Cash Inflow"].sum()
        tot_out = df_cf["Cash Outflow"].sum()
        ending_cash = df_cf["Saldo Kas Akhir"].iloc[-1] if not df_cf.empty else initial_cash
        avg_outflow = df_cf["Cash Outflow"].mean() if not df_cf.empty else 1
        runway_months = (ending_cash / avg_outflow) if avg_outflow > 0 else 99

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📥 Total Cash Inflow", f"{tot_in:,.0f}", f"{len(df_cf)} Periode")
        c2.metric("📤 Total Cash Outflow", f"{tot_out:,.0f}", f"Avg: {avg_outflow:,.0f}/bln")
        c3.metric("🏦 Saldo Kas Akhir", f"{ending_cash:,.0f}", delta=f"{(ending_cash - initial_cash):+,.0f}")
        c4.metric("⏳ Estimasi Cash Runway", f"{runway_months:.1f} Bulan", delta="Aman (>6 Bln)" if runway_months >= 6 else "Waspada (<6 Bln)")

        t1, t2 = st.tabs(["📈 Grafik Arus Kas & Likuiditas", "🤖 Analisis Treasury AI"])
        with t1:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Cash Inflow", x=df_cf["Periode"], y=df_cf["Cash Inflow"], marker=dict(color="#10b981", cornerradius=6)))
            fig.add_trace(go.Bar(name="Cash Outflow", x=df_cf["Periode"], y=df_cf["Cash Outflow"], marker=dict(color="#e11d48", cornerradius=6)))
            fig.add_trace(go.Scatter(name="Saldo Kas Akhir", x=df_cf["Periode"], y=df_cf["Saldo Kas Akhir"], mode="lines+markers", line=dict(color="#4f46e5", width=3)))
            fig.update_layout(title="Arus Kas Masuk, Keluar & Tren Saldo Kas", barmode="group", template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=380)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_cf.style.format({"Cash Inflow": "{:,.0f}", "Cash Outflow": "{:,.0f}", "Net Cash Flow": "{:+,.0f}", "Saldo Kas Akhir": "{:,.0f}"}), use_container_width=True)

        with t2:
            if st.button("✨ Generate Rekomendasi Likuiditas AI", type="primary"):
                with st.spinner("Menganalisis likuiditas..."):
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a Corporate Treasurer & CFO Advisor. Analyze cash flow, working capital, and liquidity runway in Indonesian."},
                            {"role": "user", "content": f"Saldo Awal: {initial_cash:,.0f}\nData Arus Kas:\n{df_cf.to_string(index=False)}"}
                        ],
                        model=selected_model
                    )
                    st.session_state["cf_ai"] = res.choices[0].message.content
                    st.session_state["last_module_ai"] = st.session_state["cf_ai"]
            if "cf_ai" in st.session_state:
                st.markdown(st.session_state["cf_ai"])
    else:
        st.markdown("""
<div class="empty-state-box">
<h3 style="color: #0f172a; margin-bottom: 8px;">📂 Unggah Data Arus Kas (.xlsx atau .csv)</h3>
<p style="color: #475569; font-size: 14.5px; max-width: 560px; margin: 0 auto;">
Unggah tabel arus kas dengan kolom Periode/Bulan, Kas Masuk (Inflow), dan Kas Keluar (Outflow).
</p>
</div>
""", unsafe_allow_html=True)
