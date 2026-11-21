import streamlit as st
import pandas as pd

def render(client, selected_model, to_excel_bytes):
    st.markdown("""
<div class="hero-banner">
<span class="hero-badge">APRIYO • FINANCIAL RATIOS, BEP & TAX CALCULATOR</span>
<h1>Rasio Keuangan, BEP & Pajak Cepat</h1>
<p>Hitung kesehatan rasio neraca/laba-rugi, titik impas (Break-Even Point), serta simulasi PPN & PPh Indonesia secara instan.</p>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Analisis Rasio Keuangan", "⚖️ Kalkulator BEP (Titik Impas)", "🧾 Kalkulator Pajak (PPN & PPh)"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🏛️ Data Neraca (Balance Sheet)")
            aset_lancar = st.number_input("Aset Lancar (Rp)", min_value=0, value=450000000, step=10000000)
            persediaan = st.number_input("Persediaan / Inventory (Rp)", min_value=0, value=120000000, step=5000000)
            total_aset = st.number_input("Total Aset (Rp)", min_value=1, value=950000000, step=10000000)
            liabilitas_lancar = st.number_input("Liabilitas Jangka Pendek (Rp)", min_value=1, value=200000000, step=10000000)
            total_utang = st.number_input("Total Liabilitas / Utang (Rp)", min_value=0, value=380000000, step=10000000)
            total_ekuitas = st.number_input("Total Ekuitas / Modal (Rp)", min_value=1, value=570000000, step=10000000)

        with col2:
            st.markdown("#### 📈 Data Laba Rugi (Income Statement)")
            penjualan = st.number_input("Penjualan Bersih (Rp)", min_value=1, value=1200000000, step=25000000)
            hpp = st.number_input("Harga Pokok Penjualan / COGS (Rp)", min_value=0, value=720000000, step=10000000)
            laba_bersih = st.number_input("Laba Bersih Setelah Pajak (Rp)", value=165000000, step=5000000)

        current_ratio = aset_lancar / liabilitas_lancar
        quick_ratio = (aset_lancar - persediaan) / liabilitas_lancar
        der = total_utang / total_ekuitas
        gpm = ((penjualan - hpp) / penjualan) * 100
        npm = (laba_bersih / penjualan) * 100
        roe = (laba_bersih / total_ekuitas) * 100

        st.markdown("---")
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        r1.metric("Current Ratio", f"{current_ratio:.2f}x", "Ideal > 1.5x")
        r2.metric("Quick Ratio", f"{quick_ratio:.2f}x", "Ideal > 1.0x")
        r3.metric("Debt to Equity", f"{der:.2f}x", "Ideal < 1.5x")
        r4.metric("Gross Margin", f"{gpm:.1f}%")
        r5.metric("Net Margin", f"{npm:.1f}%")
        r6.metric("ROE", f"{roe:.1f}%")

        df_ratio = pd.DataFrame({
            "Indikator Rasio": ["Current Ratio", "Quick Ratio", "Debt to Equity Ratio (DER)", "Gross Profit Margin (%)", "Net Profit Margin (%)", "Return on Equity (ROE %)"],
            "Nilai": [round(current_ratio, 2), round(quick_ratio, 2), round(der, 2), round(gpm, 2), round(npm, 2), round(roe, 2)]
        })
        st.session_state["last_module_name"] = "Analisis Rasio Keuangan"
        st.session_state["last_module_df"] = df_ratio

        if st.button("✨ Interpretasi Rasio oleh AI", type="primary"):
            with st.spinner("AI menilai kesehatan rasio..."):
                res = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a Financial Analyst. Interpret liquidity, solvency, and profitability ratios clearly in Indonesian."},
                        {"role": "user", "content": f"Hasil Rasio Keuangan:\n{df_ratio.to_string(index=False)}"}
                    ],
                    model=selected_model
                )
                st.session_state["ratio_ai"] = res.choices[0].message.content
                st.session_state["last_module_ai"] = st.session_state["ratio_ai"]
        if "ratio_ai" in st.session_state:
            st.markdown(st.session_state["ratio_ai"])

    with tab2:
        b1, b2, b3 = st.columns(3)
        fixed_cost = b1.number_input("Biaya Tetap / Fixed Cost (Rp)", min_value=0, value=75000000, step=5000000)
        price_unit = b2.number_input("Harga Jual per Unit (Rp)", min_value=1, value=150000, step=5000)
        var_unit = b3.number_input("Biaya Variabel per Unit (Rp)", min_value=0, value=90000, step=5000)

        margin_kontribusi = price_unit - var_unit
        if margin_kontribusi > 0:
            bep_unit = fixed_cost / margin_kontribusi
            bep_rp = bep_unit * price_unit
            k1, k2, k3 = st.columns(3)
            k1.metric("Contribution Margin / Unit", f"Rp {margin_kontribusi:,.0f}")
            k2.metric("🎯 BEP (Dalam Unit)", f"{bep_unit:,.0f} Unit")
            k3.metric("💰 BEP (Dalam Rupiah)", f"Rp {bep_rp:,.0f}")
        else:
            st.error("⚠️ Harga jual per unit harus lebih besar dari biaya variabel per unit.")

    with tab3:
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("#### 🧾 Simulasi PPN (11% / 12%)")
            dpp = st.number_input("Dasar Pengenaan Pajak / Nilai Transaksi (Rp)", min_value=0, value=50000000, step=1000000)
            tarif_ppn = st.selectbox("Tarif PPN:", [11, 12], index=0)
            nilai_ppn = dpp * (tarif_ppn / 100)
            st.info(f"**PPN ({tarif_ppn}%):** Rp {nilai_ppn:,.0f}  |  **Total Tagihan (Inc. PPN):** Rp {(dpp + nilai_ppn):,.0f}")

        with p2:
            st.markdown("#### 🏢 Simulasi PPh Badan & UMKM")
            jenis_pph = st.selectbox("Skema PPh:", ["PPh Final UMKM (0.5% Omzet)", "PPh Badan Umum (22% Laba Kena Pajak)"])
            dasar_pph = st.number_input("Omzet / Laba Kena Pajak (Rp)", min_value=0, value=200000000, step=5000000)
            tarif = 0.005 if "0.5%" in jenis_pph else 0.22
            pph_terutang = dasar_pph * tarif
            st.success(f"**Estimasi PPh Terutang:** Rp {pph_terutang:,.0f}")
