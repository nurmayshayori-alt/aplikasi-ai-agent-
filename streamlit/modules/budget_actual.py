import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes):
    sample_var = pd.DataFrame({
        "Category": ["Sales Revenue", "COGS", "Marketing", "Salaries", "IT & Cloud", "Operations"],
        "Budget": [150000000, 60000000, 15000000, 35000000, 8000000, 5000000],
        "Actual": [145000000, 64000000, 18500000, 35000000, 7200000, 5600000]
    })

    with st.sidebar:
        uploaded_var = st.file_uploader(
            "📂 Upload Budget vs Actual (.xlsx / .csv)",
            type=["xlsx", "xls", "csv"],
            key="upload_var"
        )
        st.download_button(
            label="📥 Contoh Excel Variance",
            data=to_excel_bytes(sample_var, "Budget_vs_Actual"),
            file_name="APRIYO_Template_Variance.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        audit_threshold = st.slider("🛡️ Batas Toleransi Audit (%)", 5, 30, 10, 1)

    st.markdown("""
<div class="hero-banner">
<span class="hero-badge">APRIYO • VARIANCE & AUDIT INTELLIGENCE</span>
<h1>Budget vs. Actuals Analytics</h1>
<p>Unggah file Excel atau CSV dengan nama kolom bebas untuk deteksi anomali anggaran & skor kesehatan finansial.</p>
</div>
""", unsafe_allow_html=True)

    if uploaded_var is not None:
        raw_df = read_any_tabular_file(uploaded_var)
        df = smart_column_mapper(
            raw_df,
            {
                "Category": ["cat", "kat", "akun", "account", "pos", "nama", "item", "desc"],
                "Budget": ["bud", "angg", "plan", "target", "rencana"],
                "Actual": ["act", "real", "aktual", "spent", "terpakai"]
            },
            key_prefix="var"
        )

        df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce").fillna(0)
        df["Actual"] = pd.to_numeric(df["Actual"], errors="coerce").fillna(0)
        df["Variance"] = df["Actual"] - df["Budget"]
        df["Variance %"] = (df["Variance"] / df["Budget"].replace(0, float("nan"))) * 100
        df["Audit Flag"] = df["Variance %"].apply(
            lambda x: "🚨 Anomali (>Batas)" if pd.notna(x) and abs(x) > audit_threshold else "✅ Normal"
        )

        # Simpan ke session_state agar bisa dibaca oleh Modul Copilot & PDF
        st.session_state["last_module_name"] = "Budget vs. Actuals Variance"
        st.session_state["last_module_df"] = df

        tot_b = df["Budget"].sum()
        tot_a = df["Actual"].sum()
        tot_v = tot_a - tot_b
        v_pct = (tot_v / tot_b * 100) if tot_b != 0 else 0
        realisasi = (tot_a / tot_b * 100) if tot_b != 0 else 0
        avg_abs_dev = df["Variance %"].abs().mean() if not df.empty else 0
        health_score = max(0, min(100, int(100 - (avg_abs_dev if pd.notna(avg_abs_dev) else 0))))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Total Budget", f"{tot_b:,.0f}", f"{len(df)} Pos Anggaran")
        c2.metric("💳 Total Actual", f"{tot_a:,.0f}", f"Rasio: {realisasi:.1f}%")
        c3.metric("📉 Total Variance", f"{tot_v:,.0f}", delta=f"{v_pct:+.1f}%", delta_color="inverse")
        c4.metric("🛡️ Budget Health Score", f"{health_score} / 100", delta="Sehat" if health_score >= 80 else "Perlu Audit")

        anomalies = df[df["Variance %"].abs() > audit_threshold]
        if not anomalies.empty:
            anom_list = ", ".join([f"{row['Category']} ({row['Variance %']:+.1f}%)" for _, row in anomalies.iterrows()])
            st.markdown(f"""
<div class="audit-alert">
<strong>🚨 Peringatan Audit Otomatis:</strong> Ditemukan <b>{len(anomalies)} kategori</b> melebihi batas toleransi ({audit_threshold}%): <b>{anom_list}</b>.
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="audit-ok">
<strong>✅ Status Audit Aman:</strong> Seluruh kategori berada dalam batas toleransi deviasi ({audit_threshold}%).
</div>
""", unsafe_allow_html=True)

        t1, t2, t3 = st.tabs(["✨ Visualisasi Grafik", "📋 Rincian & Export", "🤖 AI Audit Analyst"])

        with t1:
            col_g1, col_g2, col_g3 = st.columns([1.2, 1.2, 0.9])
            with col_g1:
                fig_area = go.Figure()
                fig_area.add_trace(go.Scatter(x=df["Category"], y=df["Budget"], name="Budget", mode="lines+markers", line=dict(color="#4f46e5", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(79, 70, 229, 0.10)"))
                fig_area.add_trace(go.Scatter(x=df["Category"], y=df["Actual"], name="Actual", mode="lines+markers", line=dict(color="#0ea5e9", width=3, shape="spline"), fill="tozeroy", fillcolor="rgba(14, 165, 233, 0.10)"))
                fig_area.update_layout(title="Tren Budget vs. Actual", template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", margin=dict(t=50, b=30, l=15, r=15), height=340)
                st.plotly_chart(fig_area, use_container_width=True)

            with col_g2:
                colors = ["#e11d48" if v > 0 else "#10b981" for v in df["Variance"]]
                fig_var = go.Figure(go.Bar(x=df["Variance"], y=df["Category"], orientation="h", marker=dict(color=colors, cornerradius=8), text=df["Variance"], texttemplate="%{text:,.0f}", textposition="auto"))
                fig_var.add_vline(x=0, line_width=1, line_dash="dot", line_color="#94a3b8")
                fig_var.update_layout(title="Deviasi (Variance) per Kategori", template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", yaxis=dict(autorange="reversed"), margin=dict(t=50, b=30, l=15, r=15), height=340)
                st.plotly_chart(fig_var, use_container_width=True)

            with col_g3:
                fig_donut = go.Figure(data=[go.Pie(labels=df["Category"], values=df["Actual"].abs(), hole=0.62, textinfo="percent", marker=dict(colors=["#4f46e5", "#0ea5e9", "#e11d48", "#10b981", "#f59e0b", "#6366f1"]))])
                fig_donut.update_layout(title="Proporsi Realisasi", template="plotly_white", paper_bgcolor="#ffffff", showlegend=True, legend=dict(orientation="h", y=-0.15, font=dict(size=10)), margin=dict(t=50, b=35, l=10, r=10), height=340)
                st.plotly_chart(fig_donut, use_container_width=True)

            top_devs = df.reindex(df["Variance"].abs().sort_values(ascending=False).index).head(3)
            rows_html = ""
            for idx, (_, r) in enumerate(top_devs.iterrows(), 1):
                badge_col = "#e11d48" if r["Variance"] > 0 else "#059669"
                status_txt = "Over Budget" if r["Variance"] > 0 else "Efisiensi"
                rows_html += f'<div class="highlight-row"><span style="color: #0f172a; font-weight: 600;">{idx}. {r["Category"]}</span><span style="color: {badge_col}; font-weight: 700;">{status_txt} {r["Variance"]:+,.0f} ({r["Variance %"]:+.1f}%)</span></div>'

            st.markdown(f"""
<div class="white-panel">
<div style="color: #0f172a; font-size: 16px; font-weight: 700; margin-bottom: 12px;">🏆 Top Deviasi & Sorotan Kategori</div>
{rows_html}
</div>
""", unsafe_allow_html=True)

        with t2:
            st.download_button("💾 Export Excel Hasil Variance", data=to_excel_bytes(df, "Variance"), file_name="APRIYO_Variance.xlsx")
            st.dataframe(df.style.format({"Budget": "{:,.2f}", "Actual": "{:,.2f}", "Variance": "{:,.2f}", "Variance %": "{:.2f}%"}), use_container_width=True)

        with t3:
            if st.button("✨ Generate Analisis Audit AI", type="primary"):
                with st.spinner("AI mengaudit data..."):
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a senior financial auditor. Provide concise executive summary and recommendations in Indonesian."},
                            {"role": "user", "content": f"Analisis Budget vs Actual (Toleransi {audit_threshold}%):\n{df.to_string(index=False)}"}
                        ],
                        model=selected_model
                    )
                    st.session_state["var_ai"] = res.choices[0].message.content
                    st.session_state["last_module_ai"] = st.session_state["var_ai"]
            if "var_ai" in st.session_state:
                st.markdown(st.session_state["var_ai"])
    else:
        st.markdown("""
<div class="empty-state-box">
<h3 style="color: #0f172a; margin-bottom: 8px;">📂 Unggah File Budget vs. Actual (.xlsx atau .csv)</h3>
<p style="color: #475569; font-size: 14.5px; max-width: 560px; margin: 0 auto;">
Nama kolom bebas (contoh: <b>Akun, Anggaran, Realisasi</b> atau <b>Category, Budget, Actual</b>). Sistem otomatis mengenali kolom Anda!
</p>
</div>
""", unsafe_allow_html=True)
