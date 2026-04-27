"""app.py — Lab Parfumo PO Pro System"""
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd

import database as db
from helpers import (current_user, is_admin, uid, uname, urole,
                      fmt_date, show_status_badge, days_until,
                      show_empty_state,
                      STATUS_COLOR, STATUS_EMOJI)

# Cookie controller สำหรับ persist session
try:
    from streamlit_cookies_controller import CookieController
    _cookie_controller = CookieController()
    HAS_COOKIES = True
except Exception:
    _cookie_controller = None
    HAS_COOKIES = False


st.set_page_config(
    page_title="Lab Parfumo PO Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Lab Parfumo Premium Styling
st.markdown("""
<meta name="color-scheme" content="light">
<style>
/* ============================================================ */
/* Lab Parfumo PO Pro — B2B Design System                       */
/* ============================================================ */

/* ===== CSS Variables ===== */
:root {
    /* Slate scale */
    --slate-900: #0F172A; --slate-800: #1E293B; --slate-700: #334155;
    --slate-600: #475569; --slate-500: #64748B; --slate-400: #94A3B8;
    --slate-300: #CBD5E1; --slate-200: #E2E8F0; --slate-100: #F1F5F9;
    --slate-50:  #F8FAFC; --white: #FFFFFF;

    /* Brand scale */
    --brand-900: #1E3A5F; --brand-800: #2E4D78; --brand-700: #3A5A8C;
    --brand-600: #4A6FA5; --brand-500: #6388B7; --brand-400: #8FA8C9;
    --brand-300: #A8C0E0; --brand-100: #E8EFF8; --brand-50:  #F4F7FB;

    /* Semantic */
    --success: #059669; --success-soft: #ECFDF5;
    --warning: #D97706; --warning-soft: #FFFBEB;
    --danger:  #DC2626; --danger-soft:  #FEF2F2;
    --info:    #2563EB; --info-soft:    #EFF6FF;

    /* Effects */
    --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.05);
    --shadow-sm: 0 2px 4px rgba(15, 23, 42, 0.06);
    --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
    --shadow-lg: 0 8px 24px rgba(15, 23, 42, 0.12);
    --shadow-brand: 0 4px 12px rgba(74, 111, 165, 0.25);

    color-scheme: light;
}

/* ===== Light theme everywhere ===== */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--slate-50);
    color: var(--slate-800);
}
[data-testid="stHeader"] { background: transparent !important; }

/* ===== Typography ===== */
h1 {
    color: var(--slate-900);
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
    line-height: 1.2;
}
h2 {
    color: var(--slate-900);
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.2px;
}
h3 {
    color: var(--slate-800);
    font-size: 14px;
    font-weight: 600;
}

/* ===== Primary button — gradient ===== */
.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"],
.stDownloadButton button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand-600), var(--brand-800));
    color: var(--white);
    border: none;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.2px;
    box-shadow: var(--shadow-sm);
    transition: all 0.15s ease;
}
.stButton button[kind="primary"]:hover,
.stFormSubmitButton button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--brand-700), var(--brand-900));
    color: var(--white);
    box-shadow: var(--shadow-brand);
    transform: translateY(-1px);
}

/* ===== Secondary button — clean white ===== */
.stButton button[kind="secondary"],
.stFormSubmitButton button[kind="secondary"],
.stDownloadButton button[kind="secondary"] {
    background: var(--white);
    color: var(--slate-700);
    border: 1px solid var(--slate-300);
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 13px;
    transition: all 0.15s ease;
}
.stButton button[kind="secondary"]:hover {
    background: var(--brand-50);
    border-color: var(--brand-600);
    color: var(--brand-700);
}

/* ===== Tabs ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid var(--slate-200);
}
.stTabs [data-baseweb="tab"] {
    color: var(--slate-500);
    font-weight: 500;
    border-radius: 6px 6px 0 0;
    padding: 8px 14px;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--brand-700) !important;
    border-bottom-color: var(--brand-700) !important;
    font-weight: 600;
}

/* ===== Inputs ===== */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input, [data-baseweb="select"] > div {
    border-radius: 8px !important;
    border-color: var(--slate-300) !important;
    transition: all 0.15s ease;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: var(--brand-600) !important;
    box-shadow: 0 0 0 3px var(--brand-100) !important;
}

/* ===== Containers (with border) ===== */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border-color: var(--slate-200) !important;
}

/* ===== Metric cards ===== */
div[data-testid="stMetric"] {
    background: var(--white);
    border: 1px solid var(--slate-200);
    border-radius: 12px;
    padding: 14px 18px;
    transition: all 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: var(--brand-300);
    box-shadow: var(--shadow-sm);
}
div[data-testid="stMetricValue"] {
    color: var(--slate-900) !important;
    font-weight: 700 !important;
    font-size: 26px !important;
}
div[data-testid="stMetricLabel"] {
    color: var(--slate-500) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
div[data-testid="stMetricDelta"] {
    font-size: 11px !important;
    font-weight: 600;
}

/* ===== Expander ===== */
[data-testid="stExpander"] {
    border-radius: 10px !important;
    border-color: var(--slate-200) !important;
}
[data-testid="stExpander"] summary {
    border-radius: 10px !important;
    background: var(--white);
}
[data-testid="stExpander"] summary:hover {
    background: var(--brand-50);
}

/* ===== Hide branding ===== */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* ============================================================ */
/* Custom Components                                            */
/* ============================================================ */

/* ----- App Top Bar (sticky header) ----- */
.app-topbar {
    background: var(--white);
    border: 1px solid var(--slate-200);
    border-radius: 12px;
    padding: 10px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: var(--shadow-xs);
}
.brand-block {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.brand-logo-sm {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--brand-600), var(--brand-800));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
    box-shadow: var(--shadow-brand);
}
.brand-text { line-height: 1.1; }
.brand-text-name {
    font-size: 15px;
    font-weight: 700;
    color: var(--slate-900);
}
.brand-text-tag {
    font-size: 10px;
    color: var(--slate-500);
    font-weight: 500;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

/* User pill */
.user-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px 4px 4px;
    background: var(--slate-50);
    border: 1px solid var(--slate-200);
    border-radius: 20px;
    font-size: 12px;
}
.user-avatar {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
    border-radius: 50%;
    color: white;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
}
.user-info-name { color: var(--slate-700); font-weight: 600; line-height: 1; }
.user-info-role { color: var(--slate-500); font-size: 10px; line-height: 1.2; }

/* ----- Page Title ----- */
.page-title-block {
    margin-bottom: 16px;
}
.page-title-text {
    font-size: 22px;
    font-weight: 700;
    color: var(--slate-900);
    line-height: 1.2;
    margin-bottom: 2px;
}
.page-title-sub {
    font-size: 13px;
    color: var(--slate-500);
}

/* ----- KPI Hero ----- */
.kpi-hero {
    background: linear-gradient(135deg, var(--brand-900), var(--brand-700));
    color: white;
    padding: 20px 24px;
    border-radius: 14px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.kpi-hero::before {
    content: '';
    position: absolute;
    top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.08), transparent);
    border-radius: 50%;
}
.kpi-hero-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 24px;
    position: relative;
    z-index: 1;
}
.kpi-label {
    font-size: 11px;
    color: rgba(255,255,255,0.7);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
}
.kpi-value-main { font-size: 32px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; }
.kpi-value-side { font-size: 22px; font-weight: 700; line-height: 1.1; margin-bottom: 2px; }
.kpi-trend {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(16, 185, 129, 0.18);
    color: #6EE7B7;
    padding: 2px 9px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}
.kpi-trend.down { background: rgba(220, 38, 38, 0.18); color: #FCA5A5; }
.kpi-meta { font-size: 11px; color: rgba(255,255,255,0.6); margin-top: 2px; }
.kpi-side {
    border-left: 1px solid rgba(255,255,255,0.15);
    padding-left: 20px;
}

/* ----- Status Pills ----- */
.lp-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid transparent;
    white-space: nowrap;
}
.lp-pill::before {
    content: '';
    width: 6px; height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
.lp-pill.pending { background: var(--warning-soft); color: var(--warning); border-color: rgba(217, 119, 6, 0.2); }
.lp-pill.pending::before { background: var(--warning); }
.lp-pill.ordered { background: var(--info-soft); color: var(--info); border-color: rgba(37, 99, 235, 0.2); }
.lp-pill.ordered::before { background: var(--info); }
.lp-pill.shipping { background: var(--brand-100); color: var(--brand-700); border-color: rgba(74, 111, 165, 0.2); }
.lp-pill.shipping::before { background: var(--brand-700); }
.lp-pill.received { background: var(--success-soft); color: var(--success); border-color: rgba(5, 150, 105, 0.2); }
.lp-pill.received::before { background: var(--success); }
.lp-pill.done { background: var(--success-soft); color: var(--success); }
.lp-pill.done::before { background: var(--success); }
.lp-pill.problem { background: var(--danger-soft); color: var(--danger); }
.lp-pill.problem::before { background: var(--danger); }
.lp-pill.cancel { background: var(--slate-100); color: var(--slate-500); }
.lp-pill.cancel::before { background: var(--slate-400); }

/* ----- Status Cards (Dashboard grid) ----- */
.status-card {
    background: var(--white);
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 12px 14px;
    transition: all 0.15s;
    position: relative;
}
.status-card:hover {
    border-color: var(--brand-600);
    box-shadow: var(--shadow-sm);
    transform: translateY(-1px);
}
.status-card-icon { font-size: 14px; margin-bottom: 4px; }
.status-card-num {
    font-size: 22px;
    font-weight: 700;
    color: var(--slate-900);
    line-height: 1;
}
.status-card-label {
    font-size: 11px;
    color: var(--slate-500);
    margin-top: 4px;
    font-weight: 500;
}
.status-card.warn::after {
    content: '';
    position: absolute;
    top: 10px; right: 10px;
    width: 6px; height: 6px;
    background: var(--warning);
    border-radius: 50%;
    box-shadow: 0 0 0 4px var(--warning-soft);
}

/* ----- Action Item Row ----- */
.action-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--slate-100);
}
.action-row:last-child { border-bottom: none; }
.action-icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 16px;
}
.action-icon.warn { background: var(--warning-soft); color: var(--warning); }
.action-icon.danger { background: var(--danger-soft); color: var(--danger); }
.action-icon.info { background: var(--info-soft); color: var(--info); }
.action-icon.brand { background: var(--brand-100); color: var(--brand-700); }
.action-icon.success { background: var(--success-soft); color: var(--success); }
.action-content { flex: 1; min-width: 0; }
.action-title-text {
    font-size: 13px;
    font-weight: 600;
    color: var(--slate-900);
    margin-bottom: 2px;
}
.action-meta-text {
    font-size: 12px;
    color: var(--slate-500);
}
.action-time-text {
    font-size: 11px;
    color: var(--slate-400);
    flex-shrink: 0;
}

/* ----- Insight Cards (small) ----- */
.insight-card {
    background: var(--white);
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.insight-label {
    font-size: 11px;
    color: var(--slate-500);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
    margin-bottom: 6px;
}
.insight-value {
    font-size: 17px;
    font-weight: 700;
    color: var(--slate-900);
    margin-bottom: 2px;
    line-height: 1.2;
}
.insight-meta {
    font-size: 12px;
    color: var(--slate-500);
}

/* ----- PO Row (table-style) ----- */
.po-row-card {
    background: var(--white);
    border: 1px solid var(--slate-200);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: all 0.15s;
}
.po-row-card:hover {
    border-color: var(--brand-300);
    box-shadow: var(--shadow-sm);
}
.po-num {
    color: var(--brand-700);
    font-weight: 700;
    font-size: 13px;
    font-family: 'SF Mono', 'Monaco', monospace;
}

/* ----- Workflow Timeline ----- */
.workflow {
    display: flex;
    gap: 0;
    align-items: flex-start;
    background: var(--slate-50);
    padding: 16px 20px;
    border-radius: 10px;
    margin-bottom: 16px;
}
.workflow-step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    min-width: 0;
    padding: 0 4px;
}
.workflow-step:not(:last-child)::after {
    content: '';
    position: absolute;
    right: -50%;
    top: 14px;
    width: 100%;
    height: 2px;
    background: var(--slate-300);
    z-index: 0;
}
.workflow-step.done:not(:last-child)::after,
.workflow-step.active:not(:last-child)::after {
    background: var(--brand-600);
}
.workflow-dot {
    width: 28px; height: 28px;
    border-radius: 50%;
    background: var(--white);
    border: 2px solid var(--slate-300);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: var(--slate-400);
    z-index: 1;
}
.workflow-step.done .workflow-dot {
    background: var(--brand-600);
    border-color: var(--brand-600);
    color: white;
}
.workflow-step.active .workflow-dot {
    background: var(--brand-600);
    border-color: var(--brand-600);
    color: white;
    box-shadow: 0 0 0 4px var(--brand-100);
}
.workflow-step.problem .workflow-dot {
    background: var(--danger);
    border-color: var(--danger);
    color: white;
}
.workflow-label {
    font-size: 11px;
    color: var(--slate-500);
    margin-top: 6px;
    font-weight: 500;
    text-align: center;
    line-height: 1.2;
}
.workflow-step.done .workflow-label,
.workflow-step.active .workflow-label {
    color: var(--slate-900);
    font-weight: 600;
}
.workflow-step.active .workflow-label { color: var(--brand-700); }

/* ----- Section Title (small uppercase) ----- */
.section-uppercase {
    font-size: 11px;
    font-weight: 700;
    color: var(--slate-500);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}

/* ----- Login Splash ----- */
.login-bg-wrapper {
    background: linear-gradient(135deg, var(--slate-900), var(--brand-900));
    margin: -40px -50px;
    padding: 60px 50px;
    border-radius: 16px;
    min-height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}
.login-card-inner {
    background: var(--white);
    border-radius: 16px;
    padding: 32px;
    width: 100%;
    max-width: 380px;
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
}
.login-logo {
    width: 64px; height: 64px;
    background: linear-gradient(135deg, var(--brand-600), var(--brand-800));
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    color: white;
    box-shadow: var(--shadow-brand);
    margin: 0 auto 16px;
}
.login-title {
    font-size: 24px;
    font-weight: 700;
    color: var(--slate-900);
    text-align: center;
    margin-bottom: 4px;
}
.login-sub {
    color: var(--slate-500);
    font-size: 13px;
    text-align: center;
    margin-bottom: 8px;
}
.login-badge {
    display: inline-block;
    background: var(--brand-100);
    color: var(--brand-700);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.login-badge-wrap { text-align: center; margin-bottom: 20px; }

/* ----- Mobile responsive ----- */
@media (max-width: 768px) {
    .kpi-hero-grid { grid-template-columns: 1fr; }
    .kpi-side { border-left: none; border-top: 1px solid rgba(255,255,255,0.15); padding-left: 0; padding-top: 14px; margin-top: 4px; }
    .workflow-label { font-size: 10px; }
    .stButton button { min-height: 40px; font-size: 13px; }
}
</style>
""", unsafe_allow_html=True)


def init_session():
    defaults = {
        'user': None,
        'mode': 'dashboard',
        'po_items': [],
        'view_po_id': None,
        'session_token': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def restore_session_from_cookie():
    """ถ้ามี token ใน cookie → restore user (สำหรับ refresh)"""
    if st.session_state.get('user'):
        return  # มีอยู่แล้ว
    if not HAS_COOKIES or not _cookie_controller:
        return
    try:
        token = _cookie_controller.get('lp_session')
        if not token:
            # Cookie อาจยังไม่ sync — ลอง rerun ครั้งเดียวให้ component โหลดเสร็จ
            # (cookies-controller มี delay ครั้งแรกหลัง refresh)
            if not st.session_state.get('_cookie_retry'):
                st.session_state['_cookie_retry'] = True
                # ใช้ getAll เป็น fallback (บางเวอร์ชันต้องเรียกแบบนี้)
                try:
                    all_cookies = _cookie_controller.getAll()
                    if all_cookies:
                        token = all_cookies.get('lp_session')
                except Exception:
                    pass
            if not token:
                return
        user = db.verify_session_token(token, max_idle_minutes=SESSION_TIMEOUT_MIN)
        if user:
            st.session_state['user'] = user
            st.session_state['session_token'] = token
            st.session_state['last_activity'] = datetime.now().isoformat()
            # ใส่กลับใน URL ด้วย
            try:
                st.query_params['t'] = token
            except Exception:
                pass
        else:
            # token หมดอายุ — ลบ cookie
            try:
                _cookie_controller.remove('lp_session')
            except Exception:
                pass
    except Exception:
        pass


def save_session_to_cookie(token):
    """บันทึก session token ลง cookie (อายุ 7 วัน — แต่ฝั่ง server เช็ค idle 5 นาที)"""
    if not HAS_COOKIES or not _cookie_controller:
        return
    try:
        _cookie_controller.set('lp_session', token,
                                 max_age=7 * 24 * 60 * 60)  # 7 days max
    except Exception:
        pass


def clear_session_cookie():
    """ลบ cookie ตอน logout"""
    if not HAS_COOKIES or not _cookie_controller:
        return
    try:
        _cookie_controller.remove('lp_session')
    except Exception:
        pass


def restore_session_from_url():
    """ถ้ามี token ใน URL → restore user (วิธีหลัก — Streamlit native)"""
    if st.session_state.get('user'):
        return
    try:
        # รับชื่อ param ทั้ง 't' (ใหม่) และ 'token' (legacy)
        token = st.query_params.get('t') or st.query_params.get('token')
        if not token:
            return
        user = db.verify_session_token(token, max_idle_minutes=SESSION_TIMEOUT_MIN)
        if user:
            st.session_state['user'] = user
            st.session_state['session_token'] = token
            st.session_state['last_activity'] = datetime.now().isoformat()
            # backup to cookie too
            save_session_to_cookie(token)
            # normalize ใน URL ให้ใช้ 't'
            try:
                if 'token' in st.query_params:
                    del st.query_params['token']
                st.query_params['t'] = token
            except Exception:
                pass
        else:
            # token หมดอายุ → ลบทั้งคู่
            try:
                if 'token' in st.query_params:
                    del st.query_params['token']
                if 't' in st.query_params:
                    del st.query_params['t']
            except Exception:
                pass
    except Exception:
        pass


init_session()


# ==================================================================
# Login
# ==================================================================

def login_page():
    """Login page — use Streamlit native components only"""
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("""
        <div style="text-align:center; padding:40px 0 24px;">
            <div style="width:64px; height:64px; margin:0 auto 16px;
                        background:linear-gradient(135deg, #4A6FA5, #3A5A8C);
                        border-radius:16px; display:flex; align-items:center;
                        justify-content:center; font-size:32px;
                        box-shadow:0 4px 12px rgba(74, 111, 165, 0.3);">📦</div>
            <div style="font-size:26px; font-weight:700; color:#1F2937;
                        margin-bottom:4px;">Lab Parfumo</div>
            <div style="font-size:13px; color:#6B7280; margin-bottom:10px;">
                Purchase Order Management System
            </div>
            <span style="display:inline-block; background:#E8EFF8; color:#3A5A8C;
                          padding:4px 12px; border-radius:12px; font-size:11px;
                          font-weight:600;">
                บริษัท ทัช ไดเวอร์เจนซ์ จำกัด
            </span>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            with st.form("login_form"):
                u = st.text_input("ชื่อผู้ใช้", placeholder="username",
                                    key="login_u")
                p = st.text_input("รหัสผ่าน", type="password",
                                    placeholder="••••••••", key="login_p")
                submitted = st.form_submit_button(
                    "🔒 เข้าสู่ระบบ", type="primary",
                    use_container_width=True
                )
                if submitted:
                    if not u or not p:
                        st.warning("⚠️ กรุณากรอกทั้งชื่อผู้ใช้และรหัสผ่าน")
                    elif db._is_account_locked(u):
                        st.error("🔒 บัญชีนี้ถูกล็อคชั่วคราว — รอ 15 นาที")
                    else:
                        with st.spinner("กำลังตรวจสอบ..."):
                            user = db.verify_user(u, p)
                        if user:
                            token = db.create_session_token(user['id'])
                            if token:
                                st.query_params['t'] = token
                                save_session_to_cookie(token)
                            st.session_state['user'] = user
                            st.session_state['session_token'] = token
                            st.session_state['last_activity'] = datetime.now().isoformat()
                            st.rerun()
                        else:
                            fails = db.get_failed_attempts_count(u)
                            remaining = 5 - fails
                            if remaining <= 0:
                                st.error("🔒 บัญชีถูกล็อคแล้ว — รอ 15 นาที")
                            elif remaining <= 2:
                                st.error(f"❌ ผิดพลาด — เหลือ **{remaining}** ครั้ง")
                            else:
                                st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

        with st.expander("ℹ️ บัญชีเริ่มต้น"):
            st.code(
                "admin / admin123     → แอดมิน\n"
                "staff1 / staff123    → ผู้สั่ง",
                language="text",
            )
            st.caption("⚠️ ครั้งแรก ระบบจะบังคับเปลี่ยนรหัสผ่าน")


# ==================================================================
# Header
# ==================================================================

def render_header():
    user = current_user()
    role_label = db.ROLES.get(user['role'], user['role'])
    emoji = "👑" if user['role'] == 'admin' else "👤"

    # ===== Layout: Brand | Main Nav | Actions =====
    if is_admin():
        c1, c2, c3 = st.columns([2.5, 6, 1.8])
    else:
        c1, c2, c3 = st.columns([2.5, 5, 1.8])

    # ----- Brand block (B2B style) -----
    with c1:
        avatar_letter = (user['full_name'] or 'U')[0].upper()
        st.markdown(f"""
        <div class="brand-block">
            <div class="brand-logo-sm">📦</div>
            <div class="brand-text">
                <div class="brand-text-name">Lab Parfumo</div>
                <div class="brand-text-tag">PO PRO</div>
            </div>
            <div style="flex:1;"></div>
            <div class="user-pill">
                <div class="user-avatar">{avatar_letter}</div>
                <div>
                    <div class="user-info-name">{user['full_name']}</div>
                    <div class="user-info-role">{role_label}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ----- Main Nav (4 ปุ่มหลัก) -----
    with c2:
        main_modes = [
            ('dashboard', '📊', 'Dashboard'),
            ('po_list', '📝', 'ใบ PO'),
            ('pending_receipt', '📦', 'รอรับของ'),
            ('withdraw', '📤', 'เบิกของ'),
        ]
        admin_modes = [
            ('equipment', '📦 Catalog'),
            ('reports', '📈 รายงาน'),
            ('users', '👥 ผู้ใช้'),
            ('settings', '⚙️ ตั้งค่า'),
        ]

        n_main = len(main_modes)
        if is_admin():
            # 4 main + 1 admin dropdown trigger
            cols = st.columns(n_main + 1)
        else:
            cols = st.columns(n_main)

        cur_mode = st.session_state['mode']
        for i, (k, icon, label) in enumerate(main_modes):
            with cols[i]:
                active = cur_mode == k
                # ใช้ icon + label ในบรรทัดเดียว
                btn_label = f"{icon} {label}"
                if st.button(btn_label, use_container_width=True,
                              type="primary" if active else "secondary",
                              key=f"nav_{k}"):
                    _switch_mode(k)

        # admin: dropdown menu
        if is_admin():
            with cols[n_main]:
                # มี active ใน admin section ไหม?
                in_admin = cur_mode in [m[0] for m in admin_modes]
                # แสดง label ตาม mode ปัจจุบัน หรือ "เครื่องมือ"
                if in_admin:
                    active_label = next(
                        (m[1] for m in admin_modes if m[0] == cur_mode),
                        "🛠️ เครื่องมือ",
                    )
                    btn_label = f"{active_label} ▾"
                else:
                    btn_label = "🛠️ เครื่องมือ ▾"

                if st.button(btn_label, use_container_width=True,
                              type="primary" if in_admin else "secondary",
                              key="nav_admin_menu"):
                    st.session_state['show_admin_menu'] = (
                        not st.session_state.get('show_admin_menu', False)
                    )
                    st.rerun()

    # ----- Right Actions -----
    with c3:
        notifs = db.get_notifications(user['id'], unread_only=True)
        n_count = len(notifs)
        nb = f"🔔 {n_count}" if n_count else "🔔"

        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            if st.button("🔍", use_container_width=True,
                          key="open_search"):
                st.session_state['show_search'] = not st.session_state.get('show_search', False)
                st.rerun()
        with ac2:
            if st.button(nb, use_container_width=True,
                          type="primary" if n_count else "secondary",
                          key="open_notif"):
                _switch_mode('notifications')
        with ac3:
            if st.button("🚪", use_container_width=True,
                          key="logout_btn"):
                _do_logout()

    # ===== Admin Dropdown Menu =====
    if is_admin() and st.session_state.get('show_admin_menu'):
        st.markdown(
            '<div style="background:#F4F6FA; border:1px solid #E5E7EB; '
            'border-radius:8px; padding:12px 16px; margin:8px 0;">'
            '<b style="color:#4A6FA5;">🛠️ เครื่องมือผู้ดูแล</b></div>',
            unsafe_allow_html=True,
        )
        am_cols = st.columns(len(admin_modes))
        for i, (k, label) in enumerate(admin_modes):
            with am_cols[i]:
                active = cur_mode == k
                if st.button(label, use_container_width=True,
                              type="primary" if active else "secondary",
                              key=f"adm_{k}"):
                    st.session_state['show_admin_menu'] = False
                    _switch_mode(k)

    st.divider()


def _switch_mode(new_mode):
    """เปลี่ยน mode + เคลียร์ state ที่เกี่ยวข้อง"""
    st.session_state['mode'] = new_mode
    st.session_state['view_po_id'] = None
    st.session_state['action_form'] = None
    st.session_state.pop('catalog_edit_id', None)
    st.session_state.pop('catalog_approve_id', None)
    st.session_state.pop('po_list_filter', None)
    st.session_state['show_admin_menu'] = False
    st.rerun()


def _do_logout():
    """logout — ลบ token + cookie + URL params"""
    tk = st.session_state.get('session_token')
    if tk:
        db.delete_session_token(tk)
    clear_session_cookie()
    try:
        for k in ('t', 'token'):
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass
    st.session_state.clear()
    init_session()
    st.rerun()


# ==================================================================
# Global Search Panel
# ==================================================================

def render_search_panel():
    """ค้นหา PO + Equipment + Categories — เปิดด้วยปุ่ม 🔍 ใน header"""
    if not st.session_state.get('show_search'):
        return

    with st.container(border=True):
        c1, c2 = st.columns([8, 1])
        with c1:
            q = st.text_input(
                "🔍 ค้นหา PO หมายเลข, ชื่อสินค้า, SKU, Supplier",
                placeholder="พิมพ์เพื่อค้นหา... (เช่น PO-2025, ขวด, supplier)",
                key="global_search_input",
                label_visibility="collapsed",
            ).strip().lower()
        with c2:
            if st.button("✕", use_container_width=True, help="ปิด"):
                st.session_state['show_search'] = False
                st.session_state.pop('global_search_input', None)
                st.rerun()

        if not q:
            st.caption("💡 ค้นจาก: หมายเลข PO, ชื่อสินค้า, SKU, ชื่อ supplier")
            return

        # ค้น PO
        all_pos = db.get_purchase_orders(user_id=uid()) if not is_admin() else db.get_purchase_orders()
        matched_pos = [
            p for p in all_pos
            if q in (p.get('po_number') or '').lower()
            or q in (p.get('supplier_name') or '').lower()
            or q in (p.get('created_by_name') or '').lower()
            or any(q in (it.get('name') or '').lower() for it in (p.get('items') or []))
        ][:10]

        # ค้น Equipment
        all_eq = db.get_equipment_list(active_only=True)
        matched_eq = [
            e for e in all_eq
            if q in (e.get('name') or '').lower()
            or q in (e.get('sku') or '').lower()
            or q in (e.get('category') or '').lower()
        ][:10]

        # แสดงผล
        total = len(matched_pos) + len(matched_eq)
        if total == 0:
            st.warning(f"ไม่พบรายการที่ตรงกับ '{q}'")
            return

        st.caption(f"พบ **{total}** รายการ")

        if matched_pos:
            st.markdown("##### 📝 ใบ PO")
            for p in matched_pos:
                emoji = STATUS_EMOJI.get(p['status'], '')
                if st.button(
                    f"{emoji} **{p['po_number']}** — {p.get('supplier_name') or 'รอ supplier'} • {len(p.get('items') or [])} รายการ",
                    key=f"sr_po_{p['id']}",
                    use_container_width=True,
                ):
                    st.session_state['mode'] = 'po_view'
                    st.session_state['view_po_id'] = p['id']
                    st.session_state['show_search'] = False
                    st.session_state.pop('global_search_input', None)
                    st.rerun()

        if matched_eq and is_admin():
            st.markdown("##### 📦 สินค้าใน Catalog")
            for e in matched_eq:
                stock = e.get('stock', 0)
                stock_emoji = "🔴" if stock == 0 else "🟡" if stock < 10 else "🟢"
                if st.button(
                    f"{stock_emoji} **{e['name']}** — SKU: {e.get('sku') or '-'} • {e.get('category', '-')}",
                    key=f"sr_eq_{e['id']}",
                    use_container_width=True,
                ):
                    st.session_state['mode'] = 'equipment'
                    st.session_state['catalog_edit_id'] = e['id']
                    st.session_state['show_search'] = False
                    st.session_state.pop('global_search_input', None)
                    st.rerun()


# ==================================================================
# Alerts
# ==================================================================

def render_alerts():
    """แสดง alert บนหัวเฉพาะหน้า dashboard และ po_list"""
    if st.session_state['mode'] not in ('dashboard', 'po_list'):
        return

    user = current_user()

    if is_admin():
        overdue = db.get_overdue_pos()
        upcoming = db.get_upcoming_pos(days=3)
    else:
        pos = db.get_purchase_orders(user_id=uid(), role=user['role'])
        today = date.today()
        overdue = [p for p in pos
                   if p.get('expected_date') and p['expected_date'] < today.isoformat()
                   and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]
        upcoming = [p for p in pos
                    if p.get('expected_date')
                    and today.isoformat() <= p['expected_date']
                    <= (today + timedelta(days=3)).isoformat()
                    and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]

    if overdue:
        po_nums = ", ".join(p['po_number'] for p in overdue[:5])
        if len(overdue) > 5:
            po_nums += f" และอีก {len(overdue) - 5} ใบ"
        st.markdown(
            f'<div class="alert" style="background:#FCEBEB; '
            f'border-left:4px solid #A32D2D; color:#5a1717;">'
            f'<b>🚨 เลยกำหนดรับของ {len(overdue)} ใบ:</b> {po_nums}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if upcoming:
        po_nums = ", ".join(p['po_number'] for p in upcoming[:5])
        if len(upcoming) > 5:
            po_nums += f" และอีก {len(upcoming) - 5} ใบ"
        st.markdown(
            f'<div class="alert" style="background:#FAEEDA; '
            f'border-left:4px solid #BA7517; color:#412402;">'
            f'<b>⏰ ใกล้ครบกำหนด {len(upcoming)} ใบ (ภายใน 3 วัน):</b> {po_nums}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ===== Pending equipment (admin only) =====
    if is_admin():
        pending_eq = db.get_pending_equipment()
        if pending_eq:
            names = ", ".join(e.get('name', '-') for e in pending_eq[:3])
            if len(pending_eq) > 3:
                names += f" และอีก {len(pending_eq) - 3} รายการ"
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div class="alert" style="background:#FFF3D6; '
                    f'border-left:4px solid #BA7517; color:#5a4202;">'
                    f'<b>🔔 มี {len(pending_eq)} รายการใหม่รออนุมัติ '
                    f'เพิ่มเข้า Catalog:</b> {names}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("⚙️ ไปดู", key="goto_pending_eq",
                              use_container_width=True):
                    st.session_state['mode'] = 'equipment'
                    st.rerun()


# ==================================================================
# Dashboard
# ==================================================================

def render_dashboard():
    """B2B Dashboard — KPI Hero + Status Grid + Action Items + Insights"""
    user = current_user()
    role = user.get('role', 'requester')
    is_adm = is_admin()

    # Page title
    today_str = date.today().strftime("%a, %d %b %Y")
    st.markdown(f"""
    <div class="page-title-block">
        <div class="page-title-text">ภาพรวมระบบ</div>
        <div class="page-title-sub">วันนี้ • {today_str}</div>
    </div>
    """, unsafe_allow_html=True)

    pos = db.get_purchase_orders(user_id=uid(), role=role)
    if not pos:
        if is_adm:
            show_empty_state(
                "📦",
                "ยินดีต้อนรับสู่ Lab Parfumo PO Pro!",
                "เริ่มต้นใช้งานง่ายๆ — เพิ่มอุปกรณ์ในระบบก่อน แล้วทีมจะสร้าง PO ได้",
                "📦 เพิ่มอุปกรณ์",
                ('equipment',),
            )
        else:
            show_empty_state(
                "📝",
                "ยินดีต้อนรับ!",
                "ยังไม่มี PO — กดปุ่มด้านล่างเพื่อสร้างใบแรก",
                "➕ สร้างใบ PO ใหม่",
                ('po_create', {'po_items': []}),
            )
        return

    valid = [p for p in pos if p['status'] != 'ยกเลิก']
    pending = [p for p in pos if p['status'] in
               ('รอจัดซื้อดำเนินการ', 'สั่งซื้อแล้ว', 'กำลังขนส่ง')]

    # =============================================================
    # KPI Hero (admin only)
    # =============================================================
    if is_adm:
        try:
            now = datetime.now()
            this_month_pos = [p for p in pos
                              if p.get('status') in ('รับของแล้ว', 'เสร็จสมบูรณ์')
                              and p.get('received_date')
                              and datetime.fromisoformat(p['received_date'].replace('Z', '+00:00')).replace(tzinfo=None).month == now.month
                              and datetime.fromisoformat(p['received_date'].replace('Z', '+00:00')).replace(tzinfo=None).year == now.year]
            last_month = (now.replace(day=1) - timedelta(days=1))
            last_month_pos = [p for p in pos
                              if p.get('status') in ('รับของแล้ว', 'เสร็จสมบูรณ์')
                              and p.get('received_date')
                              and datetime.fromisoformat(p['received_date'].replace('Z', '+00:00')).replace(tzinfo=None).month == last_month.month
                              and datetime.fromisoformat(p['received_date'].replace('Z', '+00:00')).replace(tzinfo=None).year == last_month.year]

            this_total = sum(p.get('total', 0) or 0 for p in this_month_pos)
            last_total = sum(p.get('total', 0) or 0 for p in last_month_pos)
            growth = ((this_total - last_total) / last_total * 100) if last_total else 0

            # PO ค้างนานสุด
            today = datetime.now()
            longest_days = 0
            for p in pos:
                if p['status'] in ('รอจัดซื้อดำเนินการ', 'สั่งซื้อแล้ว', 'กำลังขนส่ง'):
                    try:
                        created = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days = (today - created).days
                        if days > longest_days:
                            longest_days = days
                    except Exception:
                        pass

            # New this week
            week_ago = (today - timedelta(days=7)).isoformat()
            new_this_week = sum(1 for p in pos if p.get('created_at', '') >= week_ago)

            trend_class = "" if growth >= 0 else "down"
            trend_arrow = "↑" if growth >= 0 else "↓"
            stale_count = sum(1 for p in pos
                              if p['status'] == 'รอจัดซื้อดำเนินการ'
                              and (today - datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)).days > 3)

            st.markdown(f"""
            <div class="kpi-hero">
                <div class="kpi-hero-grid">
                    <div>
                        <div class="kpi-label">💰 ใช้จ่ายเดือนนี้</div>
                        <div class="kpi-value-main">฿{this_total:,.0f}</div>
                        <span class="kpi-trend {trend_class}">{trend_arrow} {abs(growth):.1f}% จากเดือนก่อน</span>
                    </div>
                    <div class="kpi-side">
                        <div class="kpi-label">PO ทั้งหมด</div>
                        <div class="kpi-value-side">{len(pos)}</div>
                        <div class="kpi-meta">+{new_this_week} ใบใหม่สัปดาห์นี้</div>
                    </div>
                    <div class="kpi-side">
                        <div class="kpi-label">รอดำเนินการ</div>
                        <div class="kpi-value-side">{len(pending)}</div>
                        <div class="kpi-meta">{stale_count} ใบค้างเกิน 3 วัน</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            pass

    # =============================================================
    # Status Grid (7 statuses)
    # =============================================================
    status_count = {}
    for p in pos:
        status_count[p['status']] = status_count.get(p['status'], 0) + 1

    st.markdown('<div class="section-uppercase">📊 ภาพรวมสถานะ</div>',
                unsafe_allow_html=True)
    cols = st.columns(len(db.PO_STATUSES))
    for col, status in zip(cols, db.PO_STATUSES):
        with col:
            emoji = STATUS_EMOJI.get(status, '')
            count = status_count.get(status, 0)
            short_status = status if len(status) <= 10 else status[:9] + "…"
            warn_cls = "warn" if status == "รอจัดซื้อดำเนินการ" and count > 0 else ""
            # Use clickable button styled as card
            if st.button(
                f"{emoji}\n\n# {count}\n\n{short_status}",
                key=f"status_card_{status}",
                use_container_width=True,
                help=f"ดู PO สถานะ '{status}'",
            ):
                st.session_state['mode'] = 'po_list'
                st.session_state['po_list_filter'] = status
                st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # =============================================================
    # Two columns: Action Items + Insights
    # =============================================================
    today = date.today()
    if is_adm:
        action = [p for p in pos if p['status'] in
                  ('รอจัดซื้อดำเนินการ', 'มีปัญหา')]
        action += [p for p in pos
                   if p.get('expected_date') and p['expected_date'] < today.isoformat()
                   and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]
    else:
        action = [p for p in pos if p['status'] in
                  ('รับของแล้ว', 'มีปัญหา')]
        action += [p for p in pos
                   if p.get('expected_date')
                   and today.isoformat() <= p['expected_date']
                   <= (today + timedelta(days=3)).isoformat()
                   and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]
    seen = set()
    action = [p for p in action if not (p['id'] in seen or seen.add(p['id']))]

    if is_adm:
        col_left, col_right = st.columns([3, 2])
    else:
        col_left, col_right = st.columns([1, 0.001])

    # ===== LEFT: Action Items =====
    with col_left:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
                <div style="font-size:13px; font-weight:700; color:var(--slate-900);
                            text-transform:uppercase; letter-spacing:0.6px;">
                    ⚡ ที่ต้องดำเนินการ
                    <span style="background:#DC2626; color:white; font-size:11px;
                                  padding:2px 8px; border-radius:10px; margin-left:6px;">
                        {len(action)}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not action:
                st.markdown("""
                <div style="padding:24px; text-align:center; color:var(--slate-400);
                            font-size:13px;">
                    🎉 ไม่มีงานค้าง — ทำดีมาก!
                </div>
                """, unsafe_allow_html=True)
            else:
                for po in action[:5]:
                    icon_cls = "danger" if po['status'] == 'มีปัญหา' else "warn"
                    icon = "⚠️" if po['status'] == 'มีปัญหา' else "⏰"
                    n_items = len(po.get('items', []))
                    creator = po.get('created_by_name') or "—"
                    try:
                        created = datetime.fromisoformat(po['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days_ago = (datetime.now() - created).days
                        time_label = "วันนี้" if days_ago == 0 else (f"{days_ago} วันที่แล้ว" if days_ago < 7 else f"{days_ago} วัน")
                    except Exception:
                        time_label = ""

                    st.markdown(f"""
                    <div class="action-row">
                        <div class="action-icon {icon_cls}">{icon}</div>
                        <div class="action-content">
                            <div class="action-title-text">{po['po_number']} — {po['status']}</div>
                            <div class="action-meta-text">{creator} • {n_items} รายการ</div>
                        </div>
                        <div class="action-time-text">{time_label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"ดู {po['po_number']} →",
                                  key=f"act_btn_{po['id']}",
                                  use_container_width=True):
                        st.session_state['view_po_id'] = po['id']
                        st.session_state['mode'] = 'po_view'
                        st.rerun()

    # ===== RIGHT: Insights (admin only) =====
    if is_adm:
        with col_right:
            try:
                # Top supplier
                supplier_amounts = {}
                for p in pos:
                    if p.get('supplier_name') and p.get('total'):
                        supplier_amounts[p['supplier_name']] = supplier_amounts.get(p['supplier_name'], 0) + p['total']
                top_supplier = max(supplier_amounts.items(), key=lambda x: x[1]) if supplier_amounts else None
                total_amount_all = sum(supplier_amounts.values()) or 1
                top_pct = (top_supplier[1] / total_amount_all * 100) if top_supplier else 0

                if top_supplier:
                    name = top_supplier[0]
                    short_name = name if len(name) <= 24 else name[:23] + "…"
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-label">🏆 Top Supplier เดือนนี้</div>
                        <div class="insight-value">{short_name}</div>
                        <div class="insight-meta">฿{top_supplier[1]:,.0f} • {top_pct:.0f}% ของยอดรวม</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Longest pending
                if longest_days > 0:
                    color = "var(--danger)" if longest_days > 14 else ("var(--warning)" if longest_days > 7 else "var(--brand-700)")
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-label">⏱️ PO ค้างนานสุด</div>
                        <div class="insight-value" style="color:{color};">{longest_days} วัน</div>
                        <div class="insight-meta">รอดำเนินการ</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Low stock
                eq_list = db.get_equipment_list()
                low_stock = [e for e in eq_list
                              if (e.get('stock', 0) or 0) <= 5
                              and (e.get('stock', 0) or 0) > 0]
                out_stock = [e for e in eq_list if (e.get('stock', 0) or 0) == 0]
                low_total = len(low_stock) + len(out_stock)
                if low_total > 0:
                    examples = ", ".join((e['name'][:20] for e in (low_stock + out_stock)[:3]))
                    st.markdown(f"""
                    <div class="insight-card">
                        <div class="insight-label">📦 สินค้าใกล้หมด/หมด</div>
                        <div class="insight-value">{low_total} รายการ</div>
                        <div class="insight-meta">{examples}…</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass


# ==================================================================
# Page imports
# ==================================================================

from pages_po import (render_po_list, render_po_create, render_po_view,
                       render_pending_receipt)
from pages_admin import (render_equipment, render_reports,
                          render_users, render_notifications, render_settings)
from pages_withdraw import render_withdraw


# ==================================================================
# Main
# ==================================================================

SESSION_TIMEOUT_MIN = 60  # auto logout หลังไม่ได้ใช้ 60 นาที (1 ชั่วโมง)


def check_session_timeout():
    """ตรวจ session — ถ้าไม่ใช้นานเกินกำหนด → logout"""
    last = st.session_state.get('last_activity')
    if not last:
        st.session_state['last_activity'] = datetime.now().isoformat()
        return False
    try:
        last_dt = datetime.fromisoformat(last)
        elapsed = (datetime.now() - last_dt).total_seconds() / 60
        if elapsed > SESSION_TIMEOUT_MIN:
            # ลบ cookie + clear state
            clear_session_cookie()
            st.session_state.clear()
            init_session()
            st.warning(f"⏱️ Session หมดอายุ ({SESSION_TIMEOUT_MIN} นาที) — กรุณาเข้าสู่ระบบใหม่")
            return True
    except Exception:
        pass
    st.session_state['last_activity'] = datetime.now().isoformat()
    return False


def force_change_password_page():
    """หน้าบังคับเปลี่ยนรหัสผ่านครั้งแรก"""
    user = st.session_state.get('user', {})

    st.markdown("""
    <div class="login-splash">
        <div class="login-logo">🔐</div>
        <div class="login-title">เปลี่ยนรหัสผ่าน</div>
        <div class="login-subtitle">บัญชีนี้ใช้งานครั้งแรก กรุณาตั้งรหัสใหม่</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.info(f"👤 บัญชี: **{user.get('username', '-')}** ({user.get('full_name', '-')})")

        with st.form("force_pwd_form"):
            new_pwd = st.text_input(
                "รหัสผ่านใหม่ *",
                type="password",
                placeholder="อย่างน้อย 8 ตัว มีตัวอักษร + ตัวเลข",
            )
            confirm_pwd = st.text_input(
                "ยืนยันรหัสผ่านใหม่ *",
                type="password",
            )

            st.caption(
                "📋 **กฎรหัสผ่าน:**\n"
                "• ยาวอย่างน้อย 8 ตัวอักษร\n"
                "• มีทั้งตัวอักษร และตัวเลข\n"
                "• ห้ามเหมือน username\n"
                "• ห้ามใช้รหัสที่อ่อนแอ (admin123, password)"
            )

            if st.form_submit_button("✅ เปลี่ยนรหัสผ่าน", type="primary",
                                        use_container_width=True):
                if not new_pwd or not confirm_pwd:
                    st.error("❌ กรุณากรอกครบทั้ง 2 ช่อง")
                elif new_pwd != confirm_pwd:
                    st.error("❌ รหัสผ่านยืนยันไม่ตรงกัน")
                else:
                    ok, msg = db.validate_password(new_pwd, user.get('username', ''))
                    if not ok:
                        st.error(f"❌ {msg}")
                    else:
                        success = db.update_user(user['id'], password=new_pwd)
                        if success:
                            st.session_state['user']['must_change_password'] = False
                            st.success("✅ เปลี่ยนรหัสสำเร็จ! กำลังเข้าสู่ระบบ...")
                            st.rerun()


def main():
    # ===== Restore session — try URL first (stable), then cookie =====
    restore_session_from_url()
    if not st.session_state.get('user'):
        # Cookie อาจมี delay sync — ลองอ่านอีกครั้ง
        restore_session_from_cookie()
        # ถ้ายังไม่ได้ user แต่มี token ใน session → re-verify
        if not st.session_state.get('user'):
            tk = st.session_state.get('session_token')
            if tk:
                user = db.verify_session_token(tk, max_idle_minutes=SESSION_TIMEOUT_MIN)
                if user:
                    st.session_state['user'] = user
                    st.session_state['last_activity'] = datetime.now().isoformat()

    if not st.session_state.get('user'):
        login_page()
        return

    # ===== Sync URL with token (กัน refresh แล้ว URL หาย token) =====
    tk = st.session_state.get('session_token')
    if tk:
        try:
            cur_t = st.query_params.get('t')
            if cur_t != tk:
                st.query_params['t'] = tk
        except Exception:
            pass

    # เช็ค session timeout
    if check_session_timeout():
        # ลบ token จาก DB + cookie + URL
        tk = st.session_state.get('session_token')
        if tk:
            db.delete_session_token(tk)
        clear_session_cookie()
        try:
            for k in ('t', 'token'):
                if k in st.query_params:
                    del st.query_params[k]
        except Exception:
            pass
        login_page()
        return

    # บังคับเปลี่ยนรหัสครั้งแรก
    if st.session_state['user'].get('must_change_password'):
        force_change_password_page()
        return

    # ===== Admin: เช็ค PO ค้างเกิน 3 วัน → แจ้งเตือน (1 ครั้ง/วัน) =====
    if is_admin():
        # ใช้ session flag เพื่อรันแค่ครั้งเดียวต่อ session
        if not st.session_state.get('_stale_check_done'):
            try:
                db.check_and_notify_stale_pos()
            except Exception:
                pass
            st.session_state['_stale_check_done'] = True

    render_header()
    render_search_panel()
    render_alerts()

    mode = st.session_state['mode']
    if mode == 'dashboard':
        render_dashboard()
    elif mode == 'po_list':
        render_po_list()
    elif mode == 'po_create':
        render_po_create()
    elif mode == 'po_view':
        render_po_view()
    elif mode == 'pending_receipt':
        render_pending_receipt()
    elif mode == 'withdraw':
        render_withdraw()
    elif mode == 'equipment':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_equipment()
    elif mode == 'reports':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_reports()
    elif mode == 'users':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_users()
    elif mode == 'notifications':
        render_notifications()
    elif mode == 'settings':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_settings()


if __name__ == "__main__":
    main()
