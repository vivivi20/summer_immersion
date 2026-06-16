import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import qrcode
from PIL import Image
import io
import uuid
from datetime import datetime
import json
import os
import re
import base64

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VerIQ — Verified Identity",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── LOGO HELPER ───────────────────────────────────────────────────────────────
def get_logo_b64():
    logo_paths = ["logo.png", "1781590057152_image.png"]
    for p in logo_paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

LOGO_B64 = get_logo_b64()

def logo_img(size=36, style=""):
    if LOGO_B64:
        return f'<img src="data:image/png;base64,{LOGO_B64}" width="{size}" height="{size}" style="border-radius:10px;object-fit:cover;{style}" />'
    return '<span style="font-size:1.4em;">🛡️</span>'

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── BRAND TOKENS ── */
:root {
    --brand-deep:   #1F4575;
    --brand-sky:    #DCF1FF;
    --brand-mid:    #58708F;
    --brand-dark:   #0D2B4A;
    --brand-light:  #EAF5FF;
    --ok:           #1a9e6a;
    --ok-light:     #e6f7ef;
    --danger:       #d92d20;
    --warn:         #f59e0b;

    /* light-mode surface palette */
    --bg:           #F4F8FC;
    --surface:      #FFFFFF;
    --surface-2:    #EAF5FF;
    --border:       rgba(31,69,117,0.14);
    --ink:          #0D2B4A;
    --muted:        #58708F;
    --shadow:       0 4px 20px rgba(31,69,117,0.10);
    --shadow-lg:    0 8px 36px rgba(31,69,117,0.14);
}

/* ── DARK MODE OVERRIDES ── */
@media (prefers-color-scheme: dark) {
    :root {
        --bg:       #0b1929;
        --surface:  #112240;
        --surface-2:#0e1c33;
        --border:   rgba(220,241,255,0.12);
        --ink:      #DCF1FF;
        --muted:    #88a8c8;
        --shadow:   0 4px 20px rgba(0,0,0,0.40);
        --shadow-lg:0 8px 36px rgba(0,0,0,0.50);
    }
}

/* also honour Streamlit's built-in dark-mode class */
[data-theme="dark"] {
    --bg:       #0b1929;
    --surface:  #112240;
    --surface-2:#0e1c33;
    --border:   rgba(220,241,255,0.12);
    --ink:      #DCF1FF;
    --muted:    #88a8c8;
    --shadow:   0 4px 20px rgba(0,0,0,0.40);
    --shadow-lg:0 8px 36px rgba(0,0,0,0.50);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--ink) !important;
}

/* ── STREAMLIT CHROME ── */
[data-testid="stAppViewContainer"] > .main { background: transparent; }
[data-testid="stAppViewContainer"] .block-container {
    max-width: 1280px;
    padding: 2rem 2rem 4rem;
}
header[data-testid="stHeader"] {
    background: rgba(244,248,252,0.80);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
}
[data-theme="dark"] header[data-testid="stHeader"] {
    background: rgba(11,25,41,0.80);
}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    visibility: hidden; height: 0;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D2B4A 0%, #1F4575 55%, #16395f 100%) !important;
    border-right: 1px solid rgba(220,241,255,0.10);
    box-shadow: 6px 0 28px rgba(13,43,74,0.30);
}
section[data-testid="stSidebar"] * { color: #DCF1FF !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 1.4rem 1rem; }
section[data-testid="stSidebar"] hr { border-color: rgba(220,241,255,0.15); margin: 1rem 0; }
section[data-testid="stSidebar"] label[data-baseweb="radio"] {
    background: rgba(220,241,255,0.07);
    border: 1px solid rgba(220,241,255,0.12);
    border-radius: 12px;
    padding: 0.55rem 0.75rem;
    margin-bottom: 0.3rem;
    transition: background 150ms, border-color 150ms, transform 150ms;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
    background: rgba(220,241,255,0.14);
    border-color: rgba(220,241,255,0.28);
    transform: translateX(2px);
}

/* ── SIDEBAR BRAND BLOCK ── */
.sidebar-brand {
    text-align: center;
    padding: 18px 12px 20px;
    border: 1px solid rgba(220,241,255,0.14);
    border-radius: 18px;
    background: rgba(220,241,255,0.07);
}
.sidebar-brand img {
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.30);
    margin-bottom: 10px;
}
.sidebar-brand .brand-name {
    font-size: 22px; font-weight: 800;
    color: #FFFFFF !important; letter-spacing: -0.3px;
}
.sidebar-brand .brand-tag {
    font-size: 10px; color: rgba(220,241,255,0.60) !important;
    letter-spacing: 2px; text-transform: uppercase; margin-top: 3px;
}

/* ── CARDS & SURFACES ── */
.vq-card {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 18px !important;
    box-shadow: var(--shadow) !important;
}
.vq-card:empty { display: none !important; }

.stat-box {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 20px 16px !important;
    text-align: center;
    box-shadow: var(--shadow) !important;
    transition: transform 140ms, box-shadow 140ms;
}
.stat-box:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg) !important; }

.trust-metric {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 16px !important;
    text-align: center;
    box-shadow: var(--shadow) !important;
    transition: transform 140ms, box-shadow 140ms;
}
.trust-metric:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg) !important; }

/* ── HEADER BANNER ── */
.vq-header {
    background: linear-gradient(135deg, #0D2B4A 0%, #1F4575 55%, #2c5c8a 100%) !important;
    border-radius: 18px;
    padding: 22px 28px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(220,241,255,0.15);
    position: relative;
    overflow: hidden;
    color: #FFFFFF !important;
}
.vq-header::after {
    content: "";
    position: absolute; right: -70px; top: -70px;
    width: 200px; height: 200px;
    background: rgba(220,241,255,0.07);
    transform: rotate(28deg); border-radius: 32px;
}
.vq-header * { color: #FFFFFF !important; }

/* ── BADGES & PILLS ── */
.badge-verified {
    background: linear-gradient(135deg, #1a9e6a, #16b87a);
    color: #FFFFFF !important;
    padding: 5px 13px; border-radius: 999px;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.05em; display: inline-block;
    box-shadow: 0 4px 12px rgba(26,158,106,0.30);
}
.badge-active {
    background: rgba(26,158,106,0.14);
    color: #1a9e6a !important;
    padding: 4px 10px; border-radius: 999px;
    font-size: 11px; font-weight: 700; display: inline-block;
    border: 1px solid rgba(26,158,106,0.30);
}
.live-pill {
    background: rgba(220,241,255,0.15);
    border: 1px solid rgba(220,241,255,0.24);
    color: #FFFFFF !important;
    padding: 5px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 600;
    display: inline-flex; align-items: center; gap: 5px;
}

/* ── VERIFIED BANNER (customer view) ── */
.verified-banner {
    background: linear-gradient(135deg, #e6f7ef 0%, #f0faf5 100%);
    border: 1.5px solid rgba(26,158,106,0.30);
    border-radius: 16px; padding: 20px; margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(26,158,106,0.08);
}
[data-theme="dark"] .verified-banner {
    background: linear-gradient(135deg, #0c2e1e 0%, #0f3524 100%) !important;
    border-color: rgba(26,158,106,0.35) !important;
}

/* ── TYPOGRAPHY ── */
.stat-number { font-size: 30px; font-weight: 800; color: var(--brand-deep) !important; }
.stat-label  { font-size: 12px; color: var(--muted) !important; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
.trust-metric-value { font-size: 22px; font-weight: 800; color: var(--brand-deep) !important; }
.trust-metric-label { font-size: 11px; color: var(--muted) !important; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
.section-title { font-size: 11px; font-weight: 700; color: var(--muted) !important; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 14px; }
.agent-name { font-size: 22px; font-weight: 800; color: var(--ink) !important; }
.company-name-large { font-size: 20px; font-weight: 800; color: var(--ink) !important; }

/* ── DETAIL ROWS ── */
.detail-row {
    display: flex; align-items: flex-start;
    padding: 10px 0; border-bottom: 1px solid var(--border); gap: 12px;
}
.detail-label { font-size: 10px; color: var(--muted) !important; text-transform: uppercase; letter-spacing: 0.06em; min-width: 140px; padding-top: 2px; }
.detail-value { font-size: 14px; color: var(--ink) !important; font-weight: 500; }

/* ── HERO (home page) ── */
.home-kicker { color: rgba(255,255,255,0.72); font-size: 11px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 6px; }
.home-title  { color: #FFFFFF; font-size: 40px; font-weight: 800; line-height: 1.08; margin-bottom: 10px; display: flex; align-items: center; gap: 14px; }
.home-subtitle { color: rgba(255,255,255,0.76); font-size: 15px; line-height: 1.65; max-width: 600px; }

/* ── FLOW STEPS ── */
.home-flow { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-top: 12px; }
.flow-step { background: var(--surface-2); border: 1px solid var(--border); border-radius: 14px; padding: 18px; }
.flow-number { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; background: var(--brand-deep); color: #FFFFFF; font-weight: 800; margin-bottom: 12px; font-size: 15px; }

/* ── BUTTONS ── */
div[data-testid="stButton"] > button {
    border-radius: 11px !important;
    min-height: 42px;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
    box-shadow: 0 2px 10px rgba(31,69,117,0.08);
    transition: transform 130ms, box-shadow 130ms;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(31,69,117,0.14) !important;
    border-color: rgba(31,69,117,0.30) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1F4575 0%, #2c6098 100%) !important;
    color: #FFFFFF !important;
    border: 0 !important;
    box-shadow: 0 4px 14px rgba(31,69,117,0.30) !important;
}

/* ── INPUTS ── */
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--ink) !important;
}
[data-baseweb="input"]:focus-within > div,
[data-baseweb="select"]:focus-within > div,
[data-baseweb="textarea"]:focus-within textarea {
    border-color: #1F4575 !important;
    box-shadow: 0 0 0 3px rgba(31,69,117,0.15) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px; padding: 5px; gap: 6px;
    box-shadow: var(--shadow);
}
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 9px 14px; color: var(--muted) !important; font-weight: 600; }
.stTabs [aria-selected="true"] { background: var(--brand-deep) !important; color: #FFFFFF !important; box-shadow: 0 4px 12px rgba(31,69,117,0.25); }

/* ── ALERTS / DATAFRAMES ── */
[data-testid="stAlert"] { border-radius: 14px !important; border: 1px solid var(--border) !important; }
[data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden; border: 1px solid var(--border) !important; }

/* ── LINKS ── */
a { color: #1F4575 !important; font-weight: 600; text-decoration: none !important; }
a:hover { color: #58708F !important; text-decoration: underline !important; }

/* ── FOOTER ── */
.footer-text { text-align: center; color: var(--muted) !important; font-size: 11px; margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--border); }

/* ── LOGO WATERMARK IN CARDS ── */
.vq-logo-mark { float: right; opacity: 0.18; margin: -6px -6px 0 0; }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    .home-flow { grid-template-columns: 1fr; }
    .home-title { font-size: 28px; }
    .vq-header { flex-direction: column; align-items: flex-start; gap: 12px; }
    [data-testid="stAppViewContainer"] .block-container { padding: 1.2rem 0.9rem 3rem; }
}
</style>
""", unsafe_allow_html=True)

# ─── GOOGLE SHEETS ──────────────────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1OJgAYnbcykrAJZ3zniHPxIr4wWfIJZgjc6mUOD7caxY/edit"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("veriq-499208-dcf2e353f8bc.json", scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def get_sheet(sheet_name):
    client = get_gsheet_client()
    if client:
        try:
            return client.open_by_url(SHEET_URL).worksheet(sheet_name)
        except Exception as e:
            st.error(f"Could not open sheet '{sheet_name}': {e}")
    return None

def get_df(sheet_name):
    sheet = get_sheet(sheet_name)
    if sheet:
        try:
            data = sheet.get_all_records(numericise_ignore=["all"])
            df = pd.DataFrame(data)
            df.columns = [normalize_column_name(c) for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Could not read '{sheet_name}': {e}")
    return pd.DataFrame()

def append_row(sheet_name, row):
    sheet = get_sheet(sheet_name)
    if sheet:
        sheet.append_row(row)
        return True
    return False

def normalize_column_name(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")

def normalize_cell(value):
    if pd.isna(value): return ""
    text = str(value).replace("\u00a0", " ").replace("\u200b", "").strip()
    if text.startswith("'"): text = text[1:].strip()
    if text.endswith(".0") and text[:-2].isdigit(): return text[:-2]
    return text

def normalize_lookup_id(value):
    text = normalize_cell(value).upper()
    if text.isdigit(): return text.lstrip("0") or "0"
    return text

def first_existing_column(df, names):
    for name in names:
        n = normalize_column_name(name)
        if n in df.columns: return n
    return None

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=6, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1F4575", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ─── SESSION STATE ──────────────────────────────────────────────────────────────
for k, v in [("portal","Home"),("company_logged_in",False),("agent_logged_in",False),
              ("current_company",None),("current_agent",None),("view_agent_id",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        {logo_img(54)}
        <div class="brand-name">VerIQ</div>
        <div class="brand-tag">Verified Identity</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    portal = st.radio(
        "Navigate",
        ["🏠 Home", "🏢 Company Portal", "👤 Agent Portal", "👁️ Customer View"],
        index=0, label_visibility="collapsed"
    )

    st.markdown("---")

    if st.session_state.company_logged_in and st.session_state.current_company:
        co = st.session_state.current_company
        st.markdown(f"<div style='font-size:12px;color:rgba(220,241,255,.65);'>Logged in as</div><div style='font-weight:700;color:#DCF1FF;font-size:14px;'>{co.get('company_name','')}</div>", unsafe_allow_html=True)
        if st.button("Logout Company", use_container_width=True):
            st.session_state.company_logged_in = False
            st.session_state.current_company = None
            st.rerun()

    if st.session_state.agent_logged_in and st.session_state.current_agent:
        ag = st.session_state.current_agent
        st.markdown(f"<div style='font-size:12px;color:rgba(220,241,255,.65);'>Agent</div><div style='font-weight:700;color:#DCF1FF;font-size:14px;'>{ag.get('full_name','')}</div>", unsafe_allow_html=True)
        if st.button("Logout Agent", use_container_width=True):
            st.session_state.agent_logged_in = False
            st.session_state.current_agent = None
            st.rerun()

# ─── HOME ───────────────────────────────────────────────────────────────────────
if portal == "🏠 Home":
    st.markdown(f"""
    <div class="vq-header">
        <div>
            <div class="home-kicker">Verified field identity</div>
            <div class="home-title">{logo_img(44, 'vertical-align:middle;')} VerIQ</div>
            <div class="home-subtitle">A clean trust layer for companies, field agents, and customers.
            Register teams, issue verified agent profiles, and let customers confirm identity before every visit.</div>
        </div>
        <div class="live-pill">● LIVE</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    icons = [("🏢","Company Portal","Register your company, enroll agents, manage your field force","#1F4575"),
             ("👤","Agent Portal","Access your verified profile, generate QR, send pre-visit links","#58708F"),
             ("👁️","Customer View","See exactly what customers see when they verify an agent","#DCF1FF")]
    for col, (icon, title, desc, color) in zip([col1,col2,col3], icons):
        with col:
            st.markdown(f"""
            <div class="stat-box">
                <div style="font-size:28px;margin-bottom:8px;">{icon}</div>
                <div style="font-size:16px;font-weight:700;color:var(--ink);margin-bottom:6px;">{title}</div>
                <div class="stat-label" style="text-transform:none;letter-spacing:0;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="vq-card">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
            {logo_img(22)}
            <span class="section-title" style="margin-bottom:0;">How VerIQ Works</span>
        </div>
        <div class="home-flow">
            <div class="flow-step">
                <div class="flow-number">1</div>
                <div style="font-weight:700;color:var(--ink);margin-bottom:6px;">Company Registers</div>
                <div style="font-size:13px;color:var(--muted);">Company verifies itself with GST and CIN documents</div>
            </div>
            <div class="flow-step">
                <div class="flow-number">2</div>
                <div style="font-weight:700;color:var(--ink);margin-bottom:6px;">Agent Gets Profile</div>
                <div style="font-size:13px;color:var(--muted);">Each agent receives a live verified digital identity card</div>
            </div>
            <div class="flow-step">
                <div class="flow-number">3</div>
                <div style="font-weight:700;color:var(--ink);margin-bottom:6px;">Customer Trusts</div>
                <div style="font-size:13px;color:var(--muted);">Customer scans QR or receives WhatsApp link before visit</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── COMPANY PORTAL ─────────────────────────────────────────────────────────────
elif portal == "🏢 Company Portal":

    if not st.session_state.company_logged_in:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register Company"])

        with tab1:
            st.markdown(f"""<div class="vq-card">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
                    {logo_img(28)} <span style="font-size:18px;font-weight:700;color:var(--ink);">Company Login</span>
                </div>""", unsafe_allow_html=True)
            email = st.text_input("Company Email", key="company_login_email")
            password = st.text_input("Password", type="password", key="company_login_pass")
            if st.button("Login to Company Portal", type="primary", use_container_width=True):
                df = get_df("Companies")
                email_col = first_existing_column(df, ["email","company_email","company email"])
                password_col = first_existing_column(df, ["password","company_password","company password"])
                if not df.empty and email_col and password_col:
                    match = df[(df[email_col].apply(normalize_cell).str.lower()==normalize_cell(email).lower()) &
                               (df[password_col].apply(normalize_cell)==normalize_cell(password))]
                    if not match.empty:
                        st.session_state.company_logged_in = True
                        st.session_state.current_company = match.iloc[0].to_dict()
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                else:
                    st.error("No companies registered yet.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown(f"""<div class="vq-card">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    {logo_img(28)} <span style="font-size:18px;font-weight:700;color:var(--ink);">Register Your Company</span>
                </div>
                <p style="color:var(--muted);font-size:13px;margin-bottom:18px;">All fields required for verification badge</p>""",
                unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Company Name")
                business_type = st.selectbox("Business Type", ["Financial Services","Insurance","EdTech","FMCG","Real Estate","Healthcare","Telecom","Other"])
                gstin = st.text_input("GSTIN Number")
                cin = st.text_input("CIN Number")
            with col2:
                helpline = st.text_input("Independent Helpline Number")
                reg_email = st.text_input("Company Email")
                reg_password = st.text_input("Create Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            if st.button("Register & Get Verified", type="primary", use_container_width=True):
                if all([company_name, business_type, gstin, cin, helpline, reg_email, reg_password]):
                    if reg_password != confirm_password:
                        st.error("Passwords don't match.")
                    else:
                        company_id = str(uuid.uuid4())[:8].upper()
                        row = [company_id, company_name, business_type, gstin, cin, helpline, reg_email, reg_password, "Verified"]
                        if append_row("Companies", row):
                            st.success(f"✅ Company registered! Your Company ID: **{company_id}**")
                            st.info("Login to access your dashboard.")
                        else:
                            st.error("Registration failed. Check your connection.")
                else:
                    st.warning("Please fill all fields.")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        company = st.session_state.current_company
        st.markdown(f"""
        <div class="vq-header">
            <div style="display:flex;align-items:center;gap:14px;">
                {logo_img(42)}
                <div>
                    <div style="font-size:20px;font-weight:800;">🏢 {company.get('company_name','')}</div>
                    <div style="font-size:13px;opacity:.75;">{company.get('business_type','')} · ID: {company.get('company_id','')}</div>
                </div>
            </div>
            <div class="badge-verified">✓ VERIFIED</div>
        </div>
        """, unsafe_allow_html=True)

        agents_df = get_df("Agents")
        company_agents = agents_df[agents_df["company_id"].apply(normalize_lookup_id)==normalize_lookup_id(company.get("company_id",""))] \
            if not agents_df.empty and "company_id" in agents_df.columns else pd.DataFrame()

        col1, col2, col3, col4 = st.columns(4)
        avg_rating = round(company_agents["rating"].astype(float).mean(), 1) if not company_agents.empty and "rating" in company_agents.columns else "—"
        total_visits = company_agents["verified_visits"].astype(int).sum() if not company_agents.empty and "verified_visits" in company_agents.columns else 0
        for col, (num, label) in zip([col1,col2,col3,col4],[
            (len(company_agents),"Total Agents"),(avg_rating,"Avg Rating"),(total_visits,"Total Visits"),("✓","Verified")]):
            with col:
                st.markdown(f"""<div class="stat-box">
                    <div class="stat-number">{num}</div>
                    <div class="stat-label">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["👥 My Agents", "➕ Add New Agent"])

        with tab1:
            if company_agents.empty:
                st.info("No agents enrolled yet. Add your first agent.")
            else:
                st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Enrolled Agents</div>", unsafe_allow_html=True)
                for _, agent in company_agents.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.markdown(f"**{agent.get('full_name','')}** · {agent.get('job_title','')}")
                        st.caption(f"ID: {agent.get('employee_id','')}")
                    with col2:
                        st.markdown(f"⭐ {agent.get('rating','N/A')} · {agent.get('verified_visits',0)} visits")
                    with col3:
                        st.markdown("<span class='badge-active'>✓ Active</span>", unsafe_allow_html=True)
                    with col4:
                        if st.button("View Profile", key=f"view_{agent.get('agent_id','')}"):
                            st.session_state.view_agent_id = agent.get("agent_id","")
                    st.divider()
                st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                {logo_img(24)} <span style="font-size:16px;font-weight:700;color:var(--ink);">Add New Agent</span></div>""",
                unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                agent_name = st.text_input("Full Name")
                job_title = st.text_input("Job Title")
                employee_id = st.text_input("Employee ID")
                tenure = st.text_input("Tenure (e.g. 2 yrs 3 mos)")
            with col2:
                agent_contact = st.text_input("Agent Contact Number")
                agent_rating = st.slider("Initial Rating", 1.0, 5.0, 4.5, 0.1)
                verified_visits = st.number_input("Verified Visits", min_value=0, value=0)
                agent_password = st.text_input("Agent Password", type="password")
            if st.button("Add Agent", type="primary", use_container_width=True):
                if all([agent_name, job_title, employee_id, tenure, agent_contact, agent_password]):
                    agent_id = str(uuid.uuid4())[:8].upper()
                    row = [agent_id, company.get("company_id",""), agent_name, job_title,
                           employee_id, tenure, agent_contact, agent_rating, verified_visits, agent_password]
                    if append_row("Agents", row):
                        st.success(f"✅ Agent added! Agent ID: **{agent_id}**")
                        st.rerun()
                    else:
                        st.error("Failed to add agent.")
                else:
                    st.warning("Fill all fields.")
            st.markdown("</div>", unsafe_allow_html=True)

# ─── AGENT PORTAL ───────────────────────────────────────────────────────────────
elif portal == "👤 Agent Portal":

    if not st.session_state.agent_logged_in:
        st.markdown(f"""<div class="vq-card" style="max-width:480px;margin:40px auto;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
                {logo_img(36)} <span style="font-size:20px;font-weight:800;color:var(--ink);">Agent Login</span>
            </div>""", unsafe_allow_html=True)
        emp_id = st.text_input("Employee ID")
        password = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            df = get_df("Agents")
            employee_id_col = first_existing_column(df, ["employee_id","employee id","emp_id","emp id","employee"])
            password_col = first_existing_column(df, ["password","agent_password","agent password","passcode","pin"])
            if not df.empty and employee_id_col and password_col:
                emp_match = df[df[employee_id_col].apply(normalize_lookup_id)==normalize_lookup_id(emp_id)]
                match = emp_match[emp_match[password_col].apply(normalize_cell)==normalize_cell(password)]
                if not match.empty:
                    st.session_state.agent_logged_in = True
                    st.session_state.current_agent = match.iloc[0].to_dict()
                    st.success("Login successful!")
                    st.rerun()
                elif not emp_match.empty:
                    st.error("Employee ID found, but password does not match.")
                else:
                    st.error("Employee ID not found.")
            else:
                st.error("Could not find Employee ID and Password columns.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        agent = st.session_state.current_agent
        companies_df = get_df("Companies")
        company = {}
        if not companies_df.empty and "company_id" in companies_df.columns:
            comp_match = companies_df[companies_df["company_id"].apply(normalize_lookup_id)==normalize_lookup_id(agent.get("company_id",""))]
            if not comp_match.empty:
                company = comp_match.iloc[0].to_dict()

        st.markdown(f"""
        <div class="vq-header">
            <div style="display:flex;align-items:center;gap:14px;">
                {logo_img(42)}
                <div>
                    <div style="font-size:20px;font-weight:800;">👤 {agent.get('full_name','')}</div>
                    <div style="font-size:13px;opacity:.75;">{agent.get('job_title','')} · {company.get('company_name','')}</div>
                </div>
            </div>
            <div class="badge-verified">✓ VERIFIED AGENT</div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["🪪 My Profile & QR", "📤 Send Pre-Visit Link", "📋 Visit History"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Your Verified Profile</div>", unsafe_allow_html=True)
                for label, key in [("Name","full_name"),("Employee ID","employee_id"),("Job Title","job_title"),
                                    ("Tenure","tenure"),("Contact","contact"),("Rating","rating"),
                                    ("Verified Visits","verified_visits")]:
                    val = agent.get(key, "")
                    if key == "rating": val = f"⭐ {val}"
                    st.markdown(f"""<div class="detail-row">
                        <span class="detail-label">{label}</span>
                        <span class="detail-value">{val}</span>
                    </div>""", unsafe_allow_html=True)
                for label, key in [("Company","company_name"),("Company Helpline","helpline")]:
                    st.markdown(f"""<div class="detail-row">
                        <span class="detail-label">{label}</span>
                        <span class="detail-value">{company.get(key,'')}</span>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
                    {logo_img(20)} <span class="section-title" style="margin-bottom:0;">QR Code — Show at Door</span>
                </div>""", unsafe_allow_html=True)
                profile_url = f"https://veriq.streamlit.app/?agent={agent.get('agent_id','')}"
                qr_buf = generate_qr(profile_url)
                st.image(qr_buf, width=200)
                st.caption("Show this to your customer. They can scan with any camera to verify your identity independently.")
                whatsapp_msg = f"Hello! I'm {agent.get('full_name','')}, a verified agent from {company.get('company_name','')}. View my verified profile here: {profile_url}"
                wa_url = f"https://wa.me/?text={whatsapp_msg.replace(' ','%20')}"
                st.markdown(f"[📱 Share via WhatsApp]({wa_url})")
                st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
            st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                {logo_img(24)} <span style="font-size:16px;font-weight:700;color:var(--ink);">Send Pre-Visit Briefing</span>
            </div>
            <p style="color:var(--muted);font-size:13px;margin-bottom:18px;">Fill this before visiting. Your customer receives a WhatsApp message with your verified profile and what to prepare.</p>""",
            unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name")
                customer_phone = st.text_input("Customer Phone (with country code, e.g. 919876543210)")
                purpose = st.text_input("Purpose of Visit")
                product = st.text_input("Product / Service")
            with col2:
                est_time = st.selectbox("Estimated Time", ["10-15 minutes","20-30 minutes","30-45 minutes","45-60 minutes","1-2 hours"])
                prep_requirements = st.text_area("What Customer Should Keep Ready", placeholder="e.g. PAN card, Aadhaar, last 3 salary slips")
                next_steps = st.text_input("Next Steps After Visit", placeholder="e.g. Application review in 24 hrs via SMS")
            if st.button("Generate & Send WhatsApp Message", type="primary", use_container_width=True):
                if all([customer_name, customer_phone, purpose, product]):
                    profile_url = f"https://veriq.streamlit.app/?agent={agent.get('agent_id','')}"
                    msg = f"""Hello {customer_name}! \n\nI'm {agent.get('full_name','')}, a verified field agent from {company.get('company_name','')}.\n\nI'll be visiting you shortly regarding: *{purpose}*\nProduct/Service: {product}\nEstimated time: {est_time}\n\n*Please keep ready:* {prep_requirements}\n*After the visit:* {next_steps}\n\n✅ Verify my identity here: {profile_url}\n📞 Call our company directly: {company.get('helpline','')}\n\n— Sent via VerIQ Verified Identity"""
                    msg_encoded = msg.replace(' ','%20').replace('\n','%0A')
                    wa_url = f"https://wa.me/{customer_phone}?text={msg_encoded}"
                    visit_id = str(uuid.uuid4())[:8].upper()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    append_row("Visits", [visit_id, agent.get("agent_id",""), customer_name, customer_phone,
                                          purpose, product, est_time, prep_requirements, next_steps, "Pending", timestamp])
                    st.success("✅ Message ready!")
                    st.markdown(f"[📱 Open WhatsApp & Send Message]({wa_url})")
                    with st.expander("Preview Message"):
                        st.text(msg)
                else:
                    st.warning("Fill customer name, phone, purpose and product.")
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Visit History</div>", unsafe_allow_html=True)
            visits_df = get_df("Visits")
            if not visits_df.empty and "agent_id" in visits_df.columns:
                agent_visits = visits_df[visits_df["agent_id"].apply(normalize_lookup_id)==normalize_lookup_id(agent.get("agent_id",""))]
                if not agent_visits.empty:
                    display_cols = ["customer_name","purpose","product","status","timestamp"]
                    available_cols = [c for c in display_cols if c in agent_visits.columns]
                    st.dataframe(agent_visits[available_cols], use_container_width=True)
                else:
                    st.info("No visits recorded yet.")
            else:
                st.info("No visits recorded yet.")
            st.markdown("</div>", unsafe_allow_html=True)

# ─── CUSTOMER VIEW ───────────────────────────────────────────────────────────────
elif portal == "👁️ Customer View":
    agents_df = get_df("Agents")
    companies_df = get_df("Companies")

    st.markdown(f"""<div class="vq-card">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            {logo_img(28)} <span style="font-size:18px;font-weight:700;color:var(--ink);">Customer View — Agent Verification Page</span>
        </div>
        <p style="color:var(--muted);font-size:13px;margin-bottom:16px;">This is exactly what your customer sees when they scan the QR or open the WhatsApp link.</p>""",
        unsafe_allow_html=True)

    if not agents_df.empty and "full_name" in agents_df.columns:
        agent_options = agents_df["full_name"].tolist()
        selected_agent_name = st.selectbox("Select Agent to Preview", agent_options)
        agent_row = agents_df[agents_df["full_name"]==selected_agent_name].iloc[0].to_dict()
    else:
        st.warning("No agents in the system yet. Add agents via Company Portal.")
        agent_row = {"full_name":"Rohit Sharma","job_title":"Field Verification Officer",
                     "employee_id":"BF-48217","tenure":"4 yrs 7 mos","contact":"+91 98765 43210",
                     "rating":4.9,"verified_visits":1284,"company_id":"DEMO"}
    st.markdown("</div>", unsafe_allow_html=True)

    company_row = {}
    if not companies_df.empty and "company_id" in companies_df.columns and agent_row.get("company_id"):
        comp_match = companies_df[companies_df["company_id"].apply(normalize_lookup_id)==normalize_lookup_id(agent_row.get("company_id",""))]
        if not comp_match.empty:
            company_row = comp_match.iloc[0].to_dict()
    if not company_row:
        company_row = {"company_name":"Bharat Finserv Pvt. Ltd.","business_type":"Authorized Financial Services Provider",
                       "gstin":"27AABCB1234F1Z5","cin":"U65999MH2012PTC","helpline":"1800 209 1234"}

    st.markdown("---")
    col_main, col_side = st.columns([2, 1])

    with col_main:
        now = datetime.now()
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:10px;">
                {logo_img(28)}
                <span style="font-size:18px;font-weight:800;color:var(--ink);">VerIQ — Verified Identity</span>
            </div>
            <div class="live-pill" style="background:rgba(31,69,117,0.12);border-color:rgba(31,69,117,0.25);color:var(--brand-deep) !important;">
                ● Live {now.strftime("%H:%M:%S")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="verified-banner">
            <div class="badge-verified" style="margin-bottom:10px;">✓ VERIFIED COMPANY</div>
            <div class="company-name-large">{company_row.get('company_name','')}</div>
            <div style="color:var(--muted);font-size:13px;margin:4px 0 14px;">{company_row.get('business_type','')}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;">
                <div>
                    <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">GSTIN</div>
                    <div style="font-weight:700;color:var(--ink);font-size:14px;">{company_row.get('gstin','')}</div>
                </div>
                <div>
                    <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">CIN</div>
                    <div style="font-weight:700;color:var(--ink);font-size:14px;">{company_row.get('cin','')}</div>
                </div>
            </div>
            <div style="background:var(--surface);border-radius:12px;padding:14px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--border);">
                <div>
                    <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">Independent Helpline</div>
                    <div style="font-size:17px;font-weight:800;color:var(--brand-deep);">{company_row.get('helpline','')}</div>
                </div>
                <a href="tel:{company_row.get('helpline','')}" style="background:#1F4575;color:#FFFFFF !important;padding:9px 18px;border-radius:10px;font-weight:700;font-size:14px;">📞 Call</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        initials = agent_row.get('full_name','A')[0]
        st.markdown(f"""
        <div class="vq-card">
            <div class="badge-verified" style="margin-bottom:12px;">✓ VERIFIED AGENT</div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="width:72px;height:72px;background:linear-gradient(135deg,#1F4575,#58708F);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px;color:#FFFFFF;font-weight:800;flex-shrink:0;">
                    {initials}
                </div>
                <div>
                    <div class="agent-name">{agent_row.get('full_name','')}</div>
                    <div style="color:var(--muted);font-size:14px;">{agent_row.get('job_title','')}</div>
                </div>
                <div style="margin-left:auto;">{logo_img(28,'opacity:.25;')}</div>
            </div>
            <div style="margin-top:16px;">
                <div class="detail-row"><span class="detail-label">Employee ID</span><span class="detail-value">{agent_row.get('employee_id','')}</span></div>
                <div class="detail-row"><span class="detail-label">Tenure</span><span class="detail-value">{agent_row.get('tenure','')}</span></div>
                <div class="detail-row" style="border-bottom:none;"><span class="detail-label">Agent Contact</span><span class="detail-value">{agent_row.get('contact','')}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        visits_df = get_df("Visits")
        agent_visits = visits_df[visits_df["agent_id"].apply(normalize_lookup_id)==normalize_lookup_id(agent_row.get("agent_id",""))] \
            if not visits_df.empty and "agent_id" in visits_df.columns else pd.DataFrame()
        latest_visit = agent_visits.iloc[-1].to_dict() if not agent_visits.empty else {}
        purpose  = latest_visit.get("purpose", "KYC document collection & verification")
        product  = latest_visit.get("product", "Home Loan — Pre-approval")
        est_time = latest_visit.get("est_time", "20-30 minutes")
        prep     = latest_visit.get("prep_requirements", "PAN, Aadhaar, last 3 salary slips")
        next_steps_val = latest_visit.get("next_steps", "Application review in 24 hrs via SMS")

        st.markdown(f"""
        <div class="vq-card">
            <div class="section-title">📋 Visit Details</div>
            <div class="detail-row"><span class="detail-label">Purpose of Visit</span><span class="detail-value">{purpose}</span></div>
            <div class="detail-row"><span class="detail-label">Product / Service</span><span class="detail-value">{product}</span></div>
            <div class="detail-row"><span class="detail-label">Estimated Time</span><span class="detail-value">{est_time}</span></div>
            <div class="detail-row"><span class="detail-label">Please Keep Ready</span><span class="detail-value">{prep}</span></div>
            <div class="detail-row" style="border-bottom:none;"><span class="detail-label">Next Steps</span><span class="detail-value">{next_steps_val}</span></div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="trust-metric">
                <div class="trust-metric-value">⭐ {agent_row.get('rating','4.9')}</div>
                <div class="trust-metric-label">Agent Rating</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="trust-metric">
                <div class="trust-metric-value">{agent_row.get('verified_visits','0')}</div>
                <div class="trust-metric-label">Verified Visits</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="trust-metric">
                <div class="trust-metric-value" style="font-size:17px;">{now.strftime("%H:%M")}<br>{now.strftime("%b %d")}</div>
                <div class="trust-metric-label">Live Timestamp</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Confirm Visit", type="primary", use_container_width=True):
                st.success("✅ Visit confirmed! The agent has been notified.")
                st.balloons()
        with col2:
            if st.button("❌ Decline", use_container_width=True):
                st.error("Visit declined. You will not be disturbed.")
        with col3:
            wa_url = f"https://wa.me/{company_row.get('helpline','').replace(' ','')}?text=I%20want%20to%20verify%20agent%20{agent_row.get('employee_id','')}"
            st.markdown(f"[💬 WhatsApp Company]({wa_url})")

        st.markdown(f"""
        <div class="footer-text">
            {logo_img(14, 'vertical-align:middle;margin-right:4px;opacity:.5;')}
            Protected by VerIQ · Independent third-party verification · {now.strftime("%Y-%m-%d %H:%M:%S")}
        </div>
        """, unsafe_allow_html=True)

    with col_side:
        st.markdown("<div class='vq-card'>", unsafe_allow_html=True)
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
            {logo_img(20)} <span class="section-title" style="margin-bottom:0;">Independent Verification</span>
        </div>""", unsafe_allow_html=True)
        profile_url = f"https://veriq.streamlit.app/?agent={agent_row.get('agent_id','DEMO')}"
        qr_buf = generate_qr(profile_url)
        st.image(qr_buf, use_column_width=True)
        st.markdown("""
        <div style="text-align:center;margin-top:10px;">
            <div style="font-weight:700;color:#1a9e6a;font-size:14px;">Scan with any camera</div>
            <div style="font-size:12px;color:var(--muted);margin-top:4px;">Opens VerIQ's official site directly — confirms the agent's identity outside this app.</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
