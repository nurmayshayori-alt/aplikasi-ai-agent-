import streamlit as st
import pandas as pd

def render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes):
    sample_gl = pd.DataFrame({
        "Tanggal": ["2026-10-01", "2026-10-03", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-07"],
        "No_Bukti": ["JV-001", "JV-002", "JV-003", "JV-004", "JV-005", "JV-006"],
        "Keterangan": ["Pembelian ATK", "Bayar Vendor IT", "Bayar Vendor IT", "Perjalanan Dinas", "Biaya Konsultan", "Tagihan Listrik"],
        "Nominal": [1250000, 15000000, 15000000, 50000000, 3250000, 4120000]
    })

    with st.sidebar:
        uploaded_gl = st.file_uploader(
            "📂 Upload Jurnal / Buku Besar (.xlsx / .csv)",
            type=["xlsx", "xls", "csv"],
            key="upload_gl"
        )
        st.download_button(
            label="📥 Contoh Excel Jurnal Audit",
            data=to_excel_bytes(sample_gl, "Jurnal_Umum"),
            file_name="APRIYO_Template_Audit_Jurnal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        round_limit = st.number_input("🚨 Ambang Angka Bulat (Rp)", min_value=1000000, value=10000000, step=1000000)

    st.markdown("""
<div class="hero-banner">
<span class="hero-badge">APRIYO • FORENSIC ACCOUNTING & INTERNAL AUDIT</span>
<h1>AI Fraud & Anomaly Audit</h1>
<p>Deteksi otomatis transaksi ganda (duplicate entries), jurnal akhir pekan (weekend posting), dan angka bulat mencurigakan.</p>
</div>
""", unsafe_allow_html=True)

    if uploaded_gl is not None:
        raw_gl = read_any_tabular_file(uploaded_gl)
        df_gl = smart_column_mapper(
            raw_gl,
            {
                "Tanggal": ["tgl", "date", "tanggal", "waktu"],
                "Keterangan": ["ket", "desc", "uraian", "memo", "transaksi", "nama"],
                "Nominal": ["nom", "amount", "nilai", "jumlah", "total", "rp", "debet"]
            },
            key_prefix="gl"
        )

        df_gl["Nominal"] = pd.to_numeric(df_gl["Nominal"], errors="coerce").fillna(0)
        df_gl["Tanggal_Parsed"] = pd.to_datetime(df_gl["Tanggal"], errors="coerce")

        # 1. Deteksi Duplikat (Tanggal, Keterangan, Nominal sama)
        is_dup = df_gl.duplicated(subset=["Tanggal", "Keterangan", "Nominal"], keep=False)
        # 2. Deteksi Weekend Posting (Sabtu=5, Minggu=6)
        is_weekend = df_gl["Tanggal_Parsed"].dt.dayofweek.isin([5, 6]).fillna(False)
        # 3. Deteksi Angka Bulat Besar (Habis dibagi 1.000.000 & >= ambang)
        is_round = (df_gl["Nominal"] >= round_limit) & (df_gl["Nominal"] % 1000000 == 0)

        def flag_row(idx):
            flags = []
            if is_dup.iloc[idx]:
                flags.append("🔁 Duplikat")
            if is_weekend.iloc[idx]:
                flags.append("📅 Akhir Pekan")
            if is_round.iloc[idx]:
                flags.append("🎯 Angka Bulat Besar")
            return " | ".join(flags) if flags else "✅ Bersih"

        df_gl["Status Audit"] = [flag_row(i) for i in range(len(df_gl))]
        df_view = df_gl.drop(columns=["Tanggal_Parsed"])

        st.session_state["last_module_name"] = "Forensic Fraud & Anomaly Audit"
        st.session_state["last_module_df"] = df_view

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📑 Total Baris Jurnal", f"{len(df_view):,}", f"Total: Rp {df_view['Nominal'].sum():,.0f}")
        c2.metric("🔁 Potensi Duplikat", f"{is_dup.sum()} Baris", delta="Perlu Cek" if is_dup.sum() > 0 else "Aman", delta_color="inverse")
        c3.metric("📅 Jurnal Akhir Pekan", f"{is_weekend.sum()} Baris", delta="Anomali Waktu" if is_weekend.sum() > 0 else "Normal", delta_color="inverse")
        c4.metric("🎯 Angka Bulat Besar", f"{is_round.sum()} Baris", f">= Rp {round_limit:,.0f}")

        st.subheader("📋 Kertas Kerja Audit & Deteksi Red Flags")
        st.dataframe(df_view.style.format({"Nominal": "{:,.0f}"}), use_container_width=True)

        if st.button("🕵️ Minta AI Auditor Susun Temuan & Prosedur Audit", type="primary"):
            flagged = df_view[df_view["Status Audit"] != "✅ Bersih"]
            with st.spinner("AI Auditor menganalisis red flags..."):
                res = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a Certified Fraud Examiner (CFE) and Senior Auditor. Analyze flagged journal entries and suggest audit procedures in Indonesian."},
                        {"role": "user", "content": f"Berikut transaksi yang terdeteksi anomali:\n{flagged.to_string(index=False)}"}
                    ],
                    model=selected_model
                )
                st.session_state["fraud_ai"] = res.choices[0].message.content
                st.session_state["last_module_ai"] = st.session_state["fraud_ai"]

        if "fraud_ai" in st.session_state:
            st.markdown(st.session_state["fraud_ai"])
    else:
        st.markdown("""
<div class="empty-state-box">
<h3 style="color: #0f172a; margin-bottom: 8px;">📂 Unggah Data Jurnal / Mutasi Transaksi (.xlsx atau .csv)</h3>
<p style="color: #475569; font-size: 14.5px; max-width: 560px; margin: 0 auto;">
Sistem otomatis menyisir transaksi kembar, input di hari libur/akhir pekan, dan transaksi bernilai bulat besar.
</p>
</div>
""", unsafe_allow_html=True)
