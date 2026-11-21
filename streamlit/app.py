import streamlit as st
import pandas as pd
import os
from io import BytesIO
from groq import Groq
from dotenv import load_dotenv

# Import semua modul dari folder modules/
from modules import budget_actual, scenario, cashflow, fraud_audit, ratios, copilot

# =====================================================
# 1. PAGE CONFIG & CLEAN MODERN LIGHT THEME CSS
# =====================================================
st.set_page_config(
    page_title="APRIYO | AI Financial & Accounting Suite",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #0f172a;
    }

    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }

    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 18px 22px;
        border-radius: 20px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="metric-container"] label {
        color: #64748b !important;
        font-size: 13.5px !important;
        font-weight: 600;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 24px !important;
        font-weight: 700;
    }

    .hero-banner {
        background: linear-gradient(120deg, #eef2ff 0%, #f0f9ff 60%, #ffffff 100%);
        border: 1px solid #c7d2fe;
        padding: 24px 30px;
        border-radius: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.05);
    }
    .hero-badge {
        display: inline-block;
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 8px;
        border: 1px solid #c7d2fe;
    }
    .hero-banner h1 {
        color: #0f172a !important;
        margin: 0;
        font-size: 26px;
        font-weight: 700;
    }
    .hero-banner p {
        color: #475569 !important;
        margin: 5px 0 0 0;
        font-size: 14px;
    }

    .empty-state-box {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 22px;
        padding: 44px 30px;
        text-align: center;
        margin-top: 16px;
    }

    .audit-alert {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 5px solid #e11d48;
        border-radius: 14px;
        padding: 13px 20px;
        margin-bottom: 18px;
        font-size: 13.5px;
        color: #881337;
    }
    .audit-ok {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-left: 5px solid #10b981;
        border-radius: 14px;
        padding: 13px 20px;
        margin-bottom: 18px;
        font-size: 13.5px;
        color: #065f46;
    }

    .white-panel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 20px 24px;
        margin-top: 10px;
        margin-bottom: 12px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
    }
    .highlight-row {
        background-color: #f8fafc;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 13.5px;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #ffffff;
        padding: 6px;
        border-radius: 999px;
        border: 1px solid #e2e8f0;
        width: fit-content;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 999px;
        color: #475569;
        padding: 7px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #4f46e5, #0284c7) !important;
        color: #ffffff !important;
    }

    .stButton > button, .stDownloadButton > button {
        border-radius: 999px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 2. GROQ CLIENT & SHARED SMART HELPERS
# =====================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not GROQ_API_KEY:
    st.error("🚨 GROQ_API_KEY belum diatur di Streamlit Secrets!")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

def to_excel_bytes(dataframe, sheet_name="Data"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

def read_any_tabular_file(uploaded_file):
    """Membaca file .xlsx, .xls, atau .csv secara otomatis."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=";")
    else:
        return pd.read_excel(uploaded_file)

def smart_column_mapper(df, schema_hints, key_prefix):
    """
    Mencocokkan kolom bebas (Indonesia/Inggris) secara otomatis
    dan menyediakan dropdown penyesuaian jika nama kolom unik.
    schema_hints = {"Target_Col": ["kata_kunci_1", "kata_kunci_2"]}
    """
    cols = df.columns.tolist()
    mapped = {}
    need_manual = False

    for target, keywords in schema_hints.items():
        found_idx = 0
        matched = False
        for i, c in enumerate(cols):
            c_clean = str(c).lower().strip()
            if any(kw in c_clean for kw in keywords):
                found_idx = i
                matched = True
                break
        if not matched:
            need_manual = True
        mapped[target] = cols[found_idx]

    with st.expander("⚙️ Pemetaan Kolom Otomatis (Klik jika ingin ubah pasangan kolom)", expanded=need_manual):
        st.caption("Sistem mendeteksi kolom dari file Anda secara otomatis. Sesuaikan di bawah jika diperlukan:")
        m_cols = st.columns(len(schema_hints))
        final_df = pd.DataFrame()
        for idx, (target, _) in enumerate(schema_hints.items()):
            default_ix = cols.index(mapped[target]) if mapped[target] in cols else 0
            chosen = m_cols[idx].selectbox(
                f"Kolom '{target}':",
                options=cols,
                index=default_ix,
                key=f"{key_prefix}_map_{target}"
            )
            final_df[target] = df[chosen]
    return final_df

# =====================================================
# 3. SIDEBAR NAVIGATION
# =====================================================
with st.sidebar:
    st.markdown("## ✨ APRIYO AI")
    st.caption("Intelligent Accounting & FP&A Suite")
    st.markdown("<br>", unsafe_allow_html=True)

    app_mode = st.radio(
        "🧭 Pilih Modul Akuntansi & Keuangan:",
        [
            "📊 Budget vs. Actuals",
            "🚀 Scenario Planning",
            "💧 Cash Flow & Liquidity",
            "🕵️ AI Fraud & Anomaly Audit",
            "🧮 Rasio Keuangan & Pajak",
            "🤖 Agentic Copilot & PDF"
        ],
        index=0
    )

    st.markdown("---")
    selected_model = st.selectbox(
        "🧠 Model AI (Groq)",
        ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"],
        index=0
    )
    st.caption("Mendukung unggahan **.xlsx** & **.csv** dengan nama kolom bebas.")

# =====================================================
# 4. ROUTING MODUL
# =====================================================
if app_mode == "📊 Budget vs. Actuals":
    budget_actual.render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes)

elif app_mode == "🚀 Scenario Planning":
    scenario.render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes)

elif app_mode == "💧 Cash Flow & Liquidity":
    cashflow.render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes)

elif app_mode == "🕵️ AI Fraud & Anomaly Audit":
    fraud_audit.render(client, selected_model, read_any_tabular_file, smart_column_mapper, to_excel_bytes)

elif app_mode == "🧮 Rasio Keuangan & Pajak":
    ratios.render(client, selected_model, to_excel_bytes)

elif app_mode == "🤖 Agentic Copilot & PDF":
    copilot.render(client, selected_model)
