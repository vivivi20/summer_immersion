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

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VerIQ — Verified Identity",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main { background-color: #F8FAFC; }
    
    .stApp { background-color: #F8FAFC; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A2342 0%, #1a3a5c 100%);
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stRadio label { color: white !important; }
    
    /* Cards */
    .veriq-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #E8EDF2;
    }
    
    .verified-banner {
        background: linear-gradient(135deg, #F0FFF4 0%, #E6FFED 100%);
        border: 2px solid #1DB954;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    .verified-badge {
        background: #1DB954;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    .trust-metric {
        background: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #E8EDF2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    
    .trust-metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #0A2342;
    }
    
    .trust-metric-label {
        font-size: 11px;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    .live-indicator {
        background: #1DB954;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    
    .action-confirm {
        background: #1DB954;
        color: white;
        border: none;
        padding: 14px 28px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
    }
    
    .action-decline {
        background: white;
        color: #EF4444;
        border: 2px solid #EF4444;
        padding: 14px 28px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
    }
    
    .section-title {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 12px;
    }
    
    .agent-name {
        font-size: 22px;
        font-weight: 700;
        color: #0A2342;
        margin: 0;
    }
    
    .company-name-large {
        font-size: 20px;
        font-weight: 700;
        color: #0A2342;
    }
    
    .detail-row {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #F3F4F6;
        gap: 10px;
    }
    
    .detail-label {
        font-size: 11px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 140px;
    }
    
    .detail-value {
        font-size: 14px;
        color: #1F2937;
        font-weight: 500;
    }
    
    .veriq-header {
        background: linear-gradient(135deg, #0A2342 0%, #1a3a5c 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 16px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .stat-box {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #E8EDF2;
    }
    
    .stat-number {
        font-size: 32px;
        font-weight: 700;
        color: #0A2342;
    }
    
    .stat-label {
        font-size: 13px;
        color: #6B7280;
        margin-top: 4px;
    }

    div[data-testid="stButton"] button {
        border-radius: 10px;
        font-weight: 600;
    }
    
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 10px;
        border: 1px solid #E8EDF2;
    }
    
    .footer-text {
        text-align: center;
        color: #9CA3AF;
        font-size: 12px;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid #E8EDF2;
    }
</style>
""", unsafe_allow_html=True)

# ─── GOOGLE SHEETS CONNECTION ──────────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1OJgAYnbcykrAJZ3zniHPxIr4wWfIJZgjc6mUOD7caxY/edit"
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file("veriq-499208-dcf2e353f8bc.json", scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def get_sheet(sheet_name):
    client = get_gsheet_client()
    if client:
        try:
            spreadsheet = client.open_by_url(SHEET_URL)
            return spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"Could not open sheet '{sheet_name}': {e}")
            return None
    return None

def get_df(sheet_name):
    sheet = get_sheet(sheet_name)
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Could not read data from '{sheet_name}': {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def append_row(sheet_name, row):
    sheet = get_sheet(sheet_name)
    if sheet:
        sheet.append_row(row)
        return True
    return False

def update_cell(sheet_name, row_idx, col_idx, value):
    sheet = get_sheet(sheet_name)
    if sheet:
        sheet.update_cell(row_idx, col_idx, value)
        return True
    return False

# ─── QR CODE GENERATOR ─────────────────────────────────────────────────────────
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=6, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0A2342", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
if "portal" not in st.session_state:
    st.session_state.portal = "Home"
if "company_logged_in" not in st.session_state:
    st.session_state.company_logged_in = False
if "agent_logged_in" not in st.session_state:
    st.session_state.agent_logged_in = False
if "current_company" not in st.session_state:
    st.session_state.current_company = None
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None
if "view_agent_id" not in st.session_state:
    st.session_state.view_agent_id = None

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0;'>
        <div style='font-size: 32px;'>🛡️</div>
        <div style='font-size: 22px; font-weight: 700; color: white;'>VerIQ</div>
        <div style='font-size: 11px; color: #94A3B8; letter-spacing: 1px;'>VERIFIED IDENTITY</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    portal = st.radio(
        "Navigate to:",
        ["🏠 Home", "🏢 Company Portal", "👤 Agent Portal", "👁️ Customer View"],
        index=0
    )
    
    st.markdown("---")
    
    if st.session_state.company_logged_in and st.session_state.current_company:
        st.markdown(f"**Logged in as:**\n{st.session_state.current_company.get('company_name', '')}")
        if st.button("Logout Company"):
            st.session_state.company_logged_in = False
            st.session_state.current_company = None
            st.rerun()
    
    if st.session_state.agent_logged_in and st.session_state.current_agent:
        st.markdown(f"**Agent:**\n{st.session_state.current_agent.get('full_name', '')}")
        if st.button("Logout Agent"):
            st.session_state.agent_logged_in = False
            st.session_state.current_agent = None
            st.rerun()

# ─── HOME ──────────────────────────────────────────────────────────────────────
if portal == "🏠 Home":
    st.markdown("""
    <div class='veriq-header'>
        <div>
            <div style='font-size: 28px; font-weight: 700;'>🛡️ VerIQ</div>
            <div style='font-size: 14px; color: #94A3B8; margin-top: 4px;'>Bridging the trust gap in field sales — one verified identity at a time</div>
        </div>
        <div class='live-indicator'>● LIVE</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='stat-box'>
            <div class='stat-number' style='color: #1DB954;'>🏢</div>
            <div style='font-size: 18px; font-weight: 700; color: #0A2342;'>Company Portal</div>
            <div class='stat-label'>Register your company, enroll agents, manage your field force</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='stat-box'>
            <div class='stat-number' style='color: #3B82F6;'>👤</div>
            <div style='font-size: 18px; font-weight: 700; color: #0A2342;'>Agent Portal</div>
            <div class='stat-label'>Access your verified profile, generate QR, send pre-visit links</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='stat-box'>
            <div class='stat-number' style='color: #F59E0B;'>👁️</div>
            <div style='font-size: 18px; font-weight: 700; color: #0A2342;'>Customer View</div>
            <div class='stat-label'>See exactly what your customers see when they verify an agent</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='veriq-card'>
        <div class='section-title'>How VerIQ Works</div>
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 12px;'>
            <div style='text-align: center; padding: 16px;'>
                <div style='font-size: 28px;'>1️⃣</div>
                <div style='font-weight: 600; color: #0A2342; margin: 8px 0;'>Company Registers</div>
                <div style='font-size: 13px; color: #6B7280;'>Company verifies itself with GST and CIN documents</div>
            </div>
            <div style='text-align: center; padding: 16px;'>
                <div style='font-size: 28px;'>2️⃣</div>
                <div style='font-weight: 600; color: #0A2342; margin: 8px 0;'>Agent Gets Profile</div>
                <div style='font-size: 13px; color: #6B7280;'>Each agent gets a live verified digital identity card</div>
            </div>
            <div style='text-align: center; padding: 16px;'>
                <div style='font-size: 28px;'>3️⃣</div>
                <div style='font-weight: 600; color: #0A2342; margin: 8px 0;'>Customer Trusts</div>
                <div style='font-size: 13px; color: #6B7280;'>Customer scans QR or receives WhatsApp link before visit</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── COMPANY PORTAL ────────────────────────────────────────────────────────────
elif portal == "🏢 Company Portal":
    
    if not st.session_state.company_logged_in:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register Company"])
        
        with tab1:
            st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
            st.markdown("### Company Login")
            email = st.text_input("Company Email", key="company_login_email")
            password = st.text_input("Password", type="password", key="company_login_pass")
            
            if st.button("Login to Company Portal", type="primary"):
                df = get_df("Companies")
                if not df.empty and "email" in df.columns and "password" in df.columns:
                    match = df[(df["email"].astype(str).str.strip().str.lower() == str(email).strip().lower()) & (df["password"].astype(str).str.strip() == str(password).strip())]
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
            st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
            st.markdown("### Register Your Company")
            st.caption("All fields required for verification badge")
            
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Company Name")
                business_type = st.selectbox("Business Type", [
                    "Financial Services", "Insurance", "EdTech", "FMCG",
                    "Real Estate", "Healthcare", "Telecom", "Other"
                ])
                gstin = st.text_input("GSTIN Number")
                cin = st.text_input("CIN Number")
            with col2:
                helpline = st.text_input("Independent Helpline Number")
                reg_email = st.text_input("Company Email")
                reg_password = st.text_input("Create Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Register & Get Verified", type="primary"):
                if all([company_name, business_type, gstin, cin, helpline, reg_email, reg_password]):
                    if reg_password != confirm_password:
                        st.error("Passwords don't match.")
                    else:
                        company_id = str(uuid.uuid4())[:8].upper()
                        row = [company_id, company_name, business_type, gstin, cin,
                               helpline, reg_email, reg_password, "Verified"]
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
        <div class='veriq-header'>
            <div>
                <div style='font-size: 22px; font-weight: 700;'>🏢 {company.get('company_name', '')}</div>
                <div style='font-size: 13px; color: #94A3B8;'>{company.get('business_type', '')} · ID: {company.get('company_id', '')}</div>
            </div>
            <div class='verified-badge'>✓ VERIFIED</div>
        </div>
        """, unsafe_allow_html=True)
        
        agents_df = get_df("Agents")
        company_agents = agents_df[agents_df["company_id"].astype(str) == str(company.get("company_id", ""))] if not agents_df.empty and "company_id" in agents_df.columns else pd.DataFrame()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""<div class='stat-box'>
                <div class='stat-number'>{len(company_agents)}</div>
                <div class='stat-label'>Total Agents</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            avg_rating = round(company_agents["rating"].astype(float).mean(), 1) if not company_agents.empty and "rating" in company_agents.columns else "—"
            st.markdown(f"""<div class='stat-box'>
                <div class='stat-number'>{avg_rating}</div>
                <div class='stat-label'>Avg Rating</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            total_visits = company_agents["verified_visits"].astype(int).sum() if not company_agents.empty and "verified_visits" in company_agents.columns else 0
            st.markdown(f"""<div class='stat-box'>
                <div class='stat-number'>{total_visits}</div>
                <div class='stat-label'>Total Visits</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div class='stat-box'>
                <div class='stat-number' style='color: #1DB954;'>✓</div>
                <div class='stat-label'>Company Verified</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["👥 My Agents", "➕ Add New Agent"])
        
        with tab1:
            if company_agents.empty:
                st.info("No agents enrolled yet. Add your first agent.")
            else:
                st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
                st.markdown("### Enrolled Agents")
                for _, agent in company_agents.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        st.markdown(f"**{agent.get('full_name', '')}** · {agent.get('job_title', '')}")
                        st.caption(f"ID: {agent.get('employee_id', '')}")
                    with col2:
                        st.markdown(f"⭐ {agent.get('rating', 'N/A')} · {agent.get('verified_visits', 0)} visits")
                    with col3:
                        st.markdown(f"<span class='verified-badge'>✓ Active</span>", unsafe_allow_html=True)
                    with col4:
                        if st.button("View Profile", key=f"view_{agent.get('agent_id', '')}"):
                            st.session_state.view_agent_id = agent.get("agent_id", "")
                    st.divider()
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
            st.markdown("### Add New Agent")
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
            
            if st.button("Add Agent", type="primary"):
                if all([agent_name, job_title, employee_id, tenure, agent_contact, agent_password]):
                    agent_id = str(uuid.uuid4())[:8].upper()
                    row = [agent_id, company.get("company_id", ""), agent_name, job_title,
                           employee_id, tenure, agent_contact, agent_rating, verified_visits, agent_password]
                    if append_row("Agents", row):
                        st.success(f"✅ Agent added! Agent ID: **{agent_id}**")
                        st.rerun()
                    else:
                        st.error("Failed to add agent.")
                else:
                    st.warning("Fill all fields.")
            st.markdown("</div>", unsafe_allow_html=True)

# ─── AGENT PORTAL ──────────────────────────────────────────────────────────────
elif portal == "👤 Agent Portal":
    
    if not st.session_state.agent_logged_in:
        st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
        st.markdown("### Agent Login")
        emp_id = st.text_input("Employee ID")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            df = get_df("Agents")
            if not df.empty and "employee_id" in df.columns and "password" in df.columns:
                match = df[(df["employee_id"].astype(str).str.strip() == str(emp_id).strip()) & (df["password"].astype(str).str.strip() == str(password).strip())]
                if not match.empty:
                    st.session_state.agent_logged_in = True
                    st.session_state.current_agent = match.iloc[0].to_dict()
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid Employee ID or password.")
            else:
                st.error("No agents found.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        agent = st.session_state.current_agent
        
        companies_df = get_df("Companies")
        company = {}
        if not companies_df.empty and "company_id" in companies_df.columns:
            comp_match = companies_df[companies_df["company_id"].astype(str) == str(agent.get("company_id", ""))]
            if not comp_match.empty:
                company = comp_match.iloc[0].to_dict()
        
        st.markdown(f"""
        <div class='veriq-header'>
            <div>
                <div style='font-size: 22px; font-weight: 700;'>👤 {agent.get('full_name', '')}</div>
                <div style='font-size: 13px; color: #94A3B8;'>{agent.get('job_title', '')} · {company.get('company_name', '')}</div>
            </div>
            <div class='verified-badge'>✓ VERIFIED AGENT</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["🪪 My Profile & QR", "📤 Send Pre-Visit Link", "📋 Visit History"])
        
        with tab1:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Your Verified Profile</div>", unsafe_allow_html=True)
                st.markdown(f"**Name:** {agent.get('full_name', '')}")
                st.markdown(f"**Employee ID:** {agent.get('employee_id', '')}")
                st.markdown(f"**Job Title:** {agent.get('job_title', '')}")
                st.markdown(f"**Tenure:** {agent.get('tenure', '')}")
                st.markdown(f"**Contact:** {agent.get('contact', '')}")
                st.markdown(f"**Rating:** ⭐ {agent.get('rating', 'N/A')}")
                st.markdown(f"**Verified Visits:** {agent.get('verified_visits', 0)}")
                st.markdown(f"**Company:** {company.get('company_name', '')}")
                st.markdown(f"**Company Helpline:** {company.get('helpline', '')}")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Your QR Code — Show at Door</div>", unsafe_allow_html=True)
                
                profile_url = f"https://veriq.streamlit.app/?agent={agent.get('agent_id', '')}"
                qr_buf = generate_qr(profile_url)
                st.image(qr_buf, width=200)
                
                st.caption("Show this to your customer. They can scan with any camera to verify your identity independently.")
                
                whatsapp_msg = f"Hello! I'm {agent.get('full_name', '')}, a verified agent from {company.get('company_name', '')}. View my verified profile here: {profile_url}"
                whatsapp_url = f"https://wa.me/?text={whatsapp_msg.replace(' ', '%20')}"
                st.markdown(f"[📱 Share via WhatsApp]({whatsapp_url})", unsafe_allow_html=False)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
            st.markdown("### Send Pre-Visit Briefing to Customer")
            st.caption("Fill this before visiting. Your customer receives a WhatsApp message with your verified profile and what to prepare.")
            
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name")
                customer_phone = st.text_input("Customer Phone (with country code, e.g. 919876543210)")
                purpose = st.text_input("Purpose of Visit")
                product = st.text_input("Product / Service")
            with col2:
                est_time = st.selectbox("Estimated Time", ["10-15 minutes", "20-30 minutes", "30-45 minutes", "45-60 minutes", "1-2 hours"])
                prep_requirements = st.text_area("What Customer Should Keep Ready", placeholder="e.g. PAN card, Aadhaar, last 3 salary slips")
                next_steps = st.text_input("Next Steps After Visit", placeholder="e.g. Application review in 24 hrs via SMS")
            
            if st.button("Generate & Send WhatsApp Message", type="primary"):
                if all([customer_name, customer_phone, purpose, product]):
                    profile_url = f"https://veriq.streamlit.app/?agent={agent.get('agent_id', '')}"
                    
                    msg = f"""Hello {customer_name}! 

I'm {agent.get('full_name', '')}, a verified field agent from {company.get('company_name', '')}.

I'll be visiting you shortly regarding: *{purpose}*
Product/Service: {product}
Estimated time: {est_time}

*Please keep ready:* {prep_requirements}
*After the visit:* {next_steps}

✅ Verify my identity here: {profile_url}
📞 Call our company directly: {company.get('helpline', '')}

— Sent via VerIQ Verified Identity"""
                    
                    msg_encoded = msg.replace(' ', '%20').replace('\n', '%0A')
                    wa_url = f"https://wa.me/{customer_phone}?text={msg_encoded}"
                    
                    visit_id = str(uuid.uuid4())[:8].upper()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    append_row("Visits", [visit_id, agent.get("agent_id", ""), customer_name,
                                          customer_phone, purpose, product, est_time,
                                          prep_requirements, next_steps, "Pending", timestamp])
                    
                    st.success("✅ Message ready!")
                    st.markdown(f"[📱 Open WhatsApp & Send Message]({wa_url})")
                    
                    with st.expander("Preview Message"):
                        st.text(msg)
                else:
                    st.warning("Fill customer name, phone, purpose and product.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab3:
            st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
            st.markdown("### Visit History")
            visits_df = get_df("Visits")
            if not visits_df.empty and "agent_id" in visits_df.columns:
                agent_visits = visits_df[visits_df["agent_id"].astype(str) == str(agent.get("agent_id", ""))]
                if not agent_visits.empty:
                    display_cols = ["customer_name", "purpose", "product", "status", "timestamp"]
                    available_cols = [c for c in display_cols if c in agent_visits.columns]
                    st.dataframe(agent_visits[available_cols], use_container_width=True)
                else:
                    st.info("No visits recorded yet.")
            else:
                st.info("No visits recorded yet.")
            st.markdown("</div>", unsafe_allow_html=True)

# ─── CUSTOMER VIEW ─────────────────────────────────────────────────────────────
elif portal == "👁️ Customer View":
    
    agents_df = get_df("Agents")
    companies_df = get_df("Companies")
    
    st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
    st.markdown("### 👁️ Customer View — Agent Verification Page")
    st.caption("This is exactly what your customer sees when they scan the QR or open the WhatsApp link.")
    
    if not agents_df.empty and "full_name" in agents_df.columns:
        agent_options = agents_df["full_name"].tolist()
        selected_agent_name = st.selectbox("Select Agent to Preview", agent_options)
        agent_row = agents_df[agents_df["full_name"] == selected_agent_name].iloc[0].to_dict()
    else:
        st.warning("No agents in the system yet. Add agents via Company Portal.")
        agent_row = {
            "full_name": "Rohit Sharma", "job_title": "Field Verification Officer",
            "employee_id": "BF-48217", "tenure": "4 yrs 7 mos",
            "contact": "+91 98765 43210", "rating": 4.9,
            "verified_visits": 1284, "company_id": "DEMO"
        }
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    company_row = {}
    if not companies_df.empty and "company_id" in companies_df.columns and agent_row.get("company_id"):
        comp_match = companies_df[companies_df["company_id"].astype(str) == str(agent_row.get("company_id", ""))]
        if not comp_match.empty:
            company_row = comp_match.iloc[0].to_dict()
    
    if not company_row:
        company_row = {
            "company_name": "Bharat Finserv Pvt. Ltd.",
            "business_type": "Authorized Financial Services Provider",
            "gstin": "27AABCB1234F1Z5",
            "cin": "U65999MH2012PTC",
            "helpline": "1800 209 1234"
        }
    
    st.markdown("---")
    
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        now = datetime.now()
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;'>
            <div style='font-size: 20px; font-weight: 700; color: #0A2342;'>🛡️ VerIQ — Verified Identity</div>
            <div class='live-indicator'>● Live {now.strftime("%H:%M:%S")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='verified-banner'>
            <div class='verified-badge'>✓ VERIFIED COMPANY</div>
            <div class='company-name-large'>{company_row.get('company_name', '')}</div>
            <div style='color: #4B5563; font-size: 13px; margin: 4px 0 12px;'>{company_row.get('business_type', '')}</div>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;'>
                <div><span style='font-size: 11px; color: #6B7280;'>GSTIN</span><br><strong>{company_row.get('gstin', '')}</strong></div>
                <div><span style='font-size: 11px; color: #6B7280;'>CIN</span><br><strong>{company_row.get('cin', '')}</strong></div>
            </div>
            <div style='background: white; border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-size: 11px; color: #6B7280; text-transform: uppercase;'>Independent Company Helpline</div>
                    <div style='font-size: 16px; font-weight: 700; color: #0A2342;'>{company_row.get('helpline', '')}</div>
                </div>
                <a href='tel:{company_row.get("helpline", "")}' style='background: #0A2342; color: white; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 600;'>📞 Call</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='veriq-card'>
            <div class='verified-badge'>✓ VERIFIED AGENT</div>
            <div style='display: flex; align-items: center; gap: 16px; margin-top: 8px;'>
                <div style='width: 72px; height: 72px; background: linear-gradient(135deg, #0A2342, #1DB954); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; color: white; font-weight: 700;'>
                    {agent_row.get('full_name', 'A')[0]}
                </div>
                <div>
                    <div class='agent-name'>{agent_row.get('full_name', '')}</div>
                    <div style='color: #6B7280; font-size: 14px;'>{agent_row.get('job_title', '')}</div>
                </div>
            </div>
            <div style='margin-top: 16px;'>
                <div class='detail-row'>
                    <span class='detail-label'>Employee ID</span>
                    <span class='detail-value'>{agent_row.get('employee_id', '')}</span>
                </div>
                <div class='detail-row'>
                    <span class='detail-label'>Tenure</span>
                    <span class='detail-value'>{agent_row.get('tenure', '')}</span>
                </div>
                <div class='detail-row'>
                    <span class='detail-label'>Agent Contact</span>
                    <span class='detail-value'>{agent_row.get('contact', '')}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        visits_df = get_df("Visits")
        agent_visits = visits_df[visits_df["agent_id"].astype(str) == str(agent_row.get("agent_id", ""))] if not visits_df.empty and "agent_id" in visits_df.columns else pd.DataFrame()
        latest_visit = agent_visits.iloc[-1].to_dict() if not agent_visits.empty else {}
        
        purpose = latest_visit.get("purpose", "KYC document collection & verification")
        product = latest_visit.get("product", "Home Loan — Pre-approval")
        est_time = latest_visit.get("est_time", "20-30 minutes")
        prep = latest_visit.get("prep_requirements", "PAN, Aadhaar, last 3 salary slips")
        next_steps_val = latest_visit.get("next_steps", "Application review in 24 hrs via SMS")
        
        st.markdown(f"""
        <div class='veriq-card'>
            <div class='section-title'>📋 Visit Details</div>
            <div class='detail-row'>
                <span class='detail-label'>Purpose of Visit</span>
                <span class='detail-value'>{purpose}</span>
            </div>
            <div class='detail-row'>
                <span class='detail-label'>Product / Service</span>
                <span class='detail-value'>{product}</span>
            </div>
            <div class='detail-row'>
                <span class='detail-label'>Estimated Time</span>
                <span class='detail-value'>{est_time}</span>
            </div>
            <div class='detail-row'>
                <span class='detail-label'>Please Keep Ready</span>
                <span class='detail-value'>{prep}</span>
            </div>
            <div class='detail-row' style='border-bottom: none;'>
                <span class='detail-label'>Next Steps</span>
                <span class='detail-value'>{next_steps_val}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class='trust-metric'>
                <div class='trust-metric-value'>⭐ {agent_row.get('rating', '4.9')}</div>
                <div class='trust-metric-label'>Agent Rating</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class='trust-metric'>
                <div class='trust-metric-value'>{agent_row.get('verified_visits', '0')}</div>
                <div class='trust-metric-label'>Verified Visits</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class='trust-metric'>
                <div class='trust-metric-value' style='font-size: 16px;'>{now.strftime("%H:%M")}<br>{now.strftime("%b %d")}</div>
                <div class='trust-metric-label'>Live Timestamp</div>
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
            wa_url = f"https://wa.me/{company_row.get('helpline', '').replace(' ', '')}?text=I%20want%20to%20verify%20agent%20{agent_row.get('employee_id', '')}"
            st.markdown(f"[💬 WhatsApp Company]({wa_url})")
        
        st.markdown(f"""
        <div class='footer-text'>
            Protected by VerIQ · Independent third-party verification · {now.strftime("%Y-%m-%d %H:%M:%S")}
        </div>
        """, unsafe_allow_html=True)
    
    with col_side:
        st.markdown("<div class='veriq-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>🔍 Independent Verification</div>", unsafe_allow_html=True)
        
        profile_url = f"https://veriq.streamlit.app/?agent={agent_row.get('agent_id', 'DEMO')}"
        qr_buf = generate_qr(profile_url)
        st.image(qr_buf, use_column_width=True)
        
        st.markdown("""
        <div style='text-align: center; margin-top: 8px;'>
            <strong style='color: #1DB954;'>Scan with any camera</strong><br>
            <span style='font-size: 12px; color: #6B7280;'>Opens VerIQ's official site directly — confirms the agent's identity outside this app.</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

