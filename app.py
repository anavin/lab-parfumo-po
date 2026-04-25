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

st.markdown("""
<style>
    /* ============================================ */
    /* Lab Parfumo Premium Theme                    */
    /* ============================================ */

    :root {
        --gold: #C8A47E;
        --gold-dark: #b08e6a;
        --gold-light: #E8D4BC;
        --gold-soft: rgba(200, 164, 126, 0.1);
        --bg-card: rgba(255, 255, 255, 0.04);
        --bg-card-hover: rgba(200, 164, 126, 0.08);
        --border-soft: rgba(200, 164, 126, 0.2);
        --border-active: rgba(200, 164, 126, 0.5);
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.2);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
        --shadow-gold: 0 4px 20px rgba(200, 164, 126, 0.25);
    }

    /* ----- Headings ----- */
    h1, h2, h3 {
        color: var(--gold) !important;
        letter-spacing: 0.3px;
    }
    h1 {
        background: linear-gradient(135deg, #C8A47E 0%, #E8D4BC 50%, #C8A47E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600 !important;
    }

    /* ----- Buttons (premium gradient) ----- */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 100%) !important;
        box-shadow: var(--shadow-gold) !important;
        transform: translateY(-1px);
    }
    .stButton button[kind="primary"]:active {
        transform: translateY(0);
    }
    .stButton button[kind="secondary"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-soft) !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="secondary"]:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--border-active) !important;
        transform: translateY(-1px);
    }

    /* ----- Metric cards ----- */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--bg-card) 0%, transparent 100%);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
        padding: 12px 16px;
        transition: all 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--border-active);
        background: linear-gradient(135deg, var(--bg-card-hover) 0%, transparent 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: var(--gold) !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    div[data-testid="stMetricLabel"] {
        color: rgba(232, 212, 188, 0.7) !important;
        font-weight: 400 !important;
    }

    /* ----- Containers (cards) ----- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 12px !important;
        transition: all 0.25s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--border-active) !important;
        box-shadow: var(--shadow-md);
    }

    /* ----- Inputs ----- */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background: var(--bg-card) !important;
        border-color: var(--border-soft) !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 3px var(--gold-soft) !important;
    }

    /* ----- Alerts ----- */
    .alert {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        animation: slideDown 0.3s ease-out;
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* ----- Empty state ----- */
    .empty-state {
        text-align: center;
        padding: 48px 24px;
        background: linear-gradient(180deg, var(--bg-card) 0%, transparent 100%);
        border-radius: 12px;
        border: 1px dashed var(--border-soft);
        margin: 16px 0;
    }
    .empty-icon {
        font-size: 56px;
        margin-bottom: 16px;
        opacity: 0.6;
    }
    .empty-title {
        color: var(--gold) !important;
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .empty-text {
        color: rgba(232, 212, 188, 0.7);
        font-size: 14px;
        max-width: 400px;
        margin: 0 auto 16px;
        line-height: 1.6;
    }

    /* ----- Badges ----- */
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    .badge-gold {
        background: var(--gold-soft);
        color: var(--gold);
        border: 1px solid var(--border-soft);
    }

    /* ----- Brand header (logo + name) ----- */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
    }
    .brand-logo {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: var(--shadow-gold);
    }
    .brand-name {
        font-size: 22px;
        font-weight: 600;
        background: linear-gradient(135deg, #C8A47E 0%, #E8D4BC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 0.5px;
    }

    /* ----- Login splash ----- */
    .login-splash {
        text-align: center;
        padding: 48px 24px 32px;
    }
    .login-logo {
        width: 80px;
        height: 80px;
        margin: 0 auto 16px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        box-shadow: var(--shadow-gold);
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-6px); }
    }
    .login-title {
        font-size: 32px;
        font-weight: 600;
        background: linear-gradient(135deg, #C8A47E 0%, #E8D4BC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
        letter-spacing: 1px;
    }
    .login-subtitle {
        font-size: 14px;
        color: rgba(232, 212, 188, 0.7);
        letter-spacing: 0.5px;
    }

    /* ----- Mobile responsive ----- */
    @media (max-width: 768px) {
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 16px !important; }
        div[data-testid="stMetricValue"] { font-size: 20px !important; }
        .stButton button {
            min-height: 44px !important;
            font-size: 14px !important;
        }
        div[data-testid="column"] {
            min-width: 100% !important;
            flex: 1 0 100% !important;
        }
        .login-logo { width: 64px; height: 64px; font-size: 32px; }
        .login-title { font-size: 24px; }
    }

    /* ----- Status badges ----- */
    .status-pending { background: rgba(136, 136, 136, 0.15); color: #aaa; }
    .status-ordered { background: rgba(15, 110, 86, 0.15); color: #5DCAA5; }
    .status-shipping { background: rgba(186, 117, 23, 0.15); color: #FAC775; }
    .status-received { background: rgba(29, 158, 117, 0.15); color: #5DCAA5; }
    .status-issue { background: rgba(163, 45, 45, 0.15); color: #F09595; }
    .status-done { background: rgba(39, 80, 10, 0.15); color: #97C459; }
    .status-cancelled { background: rgba(163, 45, 45, 0.15); color: #999; }

    /* ----- Animations on page load ----- */
    .stMarkdown, .element-container {
        animation: fadeIn 0.4s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* ----- Scrollbar polish ----- */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: var(--border-soft);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--border-active);
    }

    /* ----- Hide Streamlit branding for clean look ----- */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }
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
            return
        user = db.verify_session_token(token, max_idle_minutes=SESSION_TIMEOUT_MIN)
        if user:
            st.session_state['user'] = user
            st.session_state['session_token'] = token
            st.session_state['last_activity'] = datetime.now().isoformat()
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
    st.markdown("""
    <div class="login-splash">
        <div class="login-logo">📦</div>
        <div class="login-title">Lab Parfumo</div>
        <div class="login-subtitle">PO Management System</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login_form"):
            st.markdown("### 🔒 เข้าสู่ระบบ")
            u = st.text_input("ชื่อผู้ใช้", placeholder="username")
            p = st.text_input("รหัสผ่าน", type="password", placeholder="••••••••")
            if st.form_submit_button("เข้าสู่ระบบ", type="primary",
                                       use_container_width=True):
                if not u or not p:
                    st.warning("⚠️ กรุณากรอกทั้งชื่อผู้ใช้และรหัสผ่าน")
                # เช็คว่าโดนล็อคไหม
                elif db._is_account_locked(u):
                    st.error("🔒 บัญชีนี้ถูกล็อคชั่วคราว — รอ 15 นาที แล้วลองใหม่ "
                             "(ผิดพลาดเกิน 5 ครั้งใน 15 นาที)")
                else:
                    with st.spinner("กำลังตรวจสอบ..."):
                        user = db.verify_user(u, p)
                    if user:
                        # สร้าง session token + ใส่ใน URL (refresh จะกลับมา login)
                        token = db.create_session_token(user['id'])
                        if token:
                            st.query_params['t'] = token
                            save_session_to_cookie(token)  # backup
                        st.session_state['user'] = user
                        st.session_state['session_token'] = token
                        st.session_state['last_activity'] = datetime.now().isoformat()
                        st.rerun()
                    else:
                        # นับจำนวนผิด
                        fails = db.get_failed_attempts_count(u)
                        remaining = 5 - fails
                        if remaining <= 0:
                            st.error("🔒 บัญชีถูกล็อคแล้ว — รอ 15 นาที")
                        elif remaining <= 2:
                            st.error(f"❌ ผิดพลาด — เหลือ **{remaining}** ครั้ง ก่อนถูกล็อค")
                        else:
                            st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

        with st.expander("ℹ️ บัญชีเริ่มต้น (สำหรับทดสอบ)"):
            st.code(
                "admin / admin123     → แอดมิน + จัดซื้อ (เห็นทุกอย่าง)\n"
                "staff1 / staff123    → ผู้สั่ง (ไม่เห็นราคา/supplier)",
                language="text",
            )
            st.caption("⚠️ **สำคัญ:** หลังใช้ครั้งแรก ระบบจะบังคับให้เปลี่ยนรหัสผ่าน")


# ==================================================================
# Header
# ==================================================================

def render_header():
    user = current_user()
    role_label = db.ROLES.get(user['role'], user['role'])
    emoji = "👑" if user['role'] == 'admin' else "👤"

    c1, c2, c3 = st.columns([3, 5, 2])
    with c1:
        st.markdown(f"""
        <div class="brand-header">
            <div class="brand-logo">📦</div>
            <div>
                <div class="brand-name">Lab Parfumo</div>
                <div style="font-size: 11px; color: rgba(232, 212, 188, 0.6); letter-spacing: 0.5px; margin-top: -2px;">
                    {emoji} {user['full_name']} • {role_label}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        modes = [('dashboard', '📊 Dashboard'), ('po_list', '📝 ใบ PO')]
        # เมนู "รอรับของ" — staff ทุกคนเห็น (รวม admin)
        modes.append(('pending_receipt', '📦 รอรับของ'))
        if is_admin():
            modes += [
                ('equipment', '📦 Catalog'),
                ('reports', '📈 รายงาน'),
                ('users', '👥 ผู้ใช้'),
            ]
        nc = st.columns(len(modes))
        for i, (k, label) in enumerate(modes):
            with nc[i]:
                active = st.session_state['mode'] == k
                if st.button(label, use_container_width=True,
                             type="primary" if active else "secondary",
                             key=f"nav_{k}"):
                    # เคลียร์ state ทั้งหมดเมื่อเปลี่ยนหน้า
                    st.session_state['mode'] = k
                    st.session_state['view_po_id'] = None
                    st.session_state['action_form'] = None
                    st.session_state.pop('catalog_edit_id', None)
                    st.session_state.pop('po_list_filter', None)
                    st.rerun()
    with c3:
        notifs = db.get_notifications(user['id'], unread_only=True)
        nb = f"🔔 ({len(notifs)})" if notifs else "🔔"
        nc1, nc2 = st.columns(2)
        with nc1:
            if st.button(nb, use_container_width=True,
                         type="primary" if notifs else "secondary"):
                st.session_state['mode'] = 'notifications'
                st.session_state['view_po_id'] = None
                st.session_state['action_form'] = None
                st.session_state.pop('catalog_edit_id', None)
                st.rerun()
        with nc2:
            if st.button("🚪", use_container_width=True, help="ออกจากระบบ"):
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
                st.session_state.clear()
                init_session()
                st.rerun()
    st.divider()


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


# ==================================================================
# Dashboard
# ==================================================================

def render_dashboard():
    user = current_user()
    role = user.get('role', 'requester')
    is_adm = is_admin()

    st.markdown("## 📊 Dashboard")

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
                "ยังไม่มี PO — กดปุ่มด้านล่างเพื่อสร้างใบแรก ระบบจะแจ้งแอดมินอัตโนมัติ",
                "➕ สร้างใบ PO ใหม่",
                ('po_create', {'po_items': []}),
            )
        return

    # KPI — คลิกการ์ดเพื่อ filter
    valid = [p for p in pos if p['status'] != 'ยกเลิก']
    pending = [p for p in pos if p['status'] in
               ('รอจัดซื้อดำเนินการ', 'สั่งซื้อแล้ว', 'กำลังขนส่ง')]
    completed = [p for p in pos if p['status'] in
                 ('รับของแล้ว', 'เสร็จสมบูรณ์')]
    issues = [p for p in pos if p['status'] == 'มีปัญหา']

    def goto_po_list(filter_status=None):
        st.session_state['mode'] = 'po_list'
        if filter_status:
            st.session_state['po_list_filter'] = filter_status
        st.rerun()

    # CSS ทำให้ปุ่ม KPI ดูเหมือน metric card
    st.markdown("""
    <style>
        .kpi-button button {
            width: 100% !important;
            height: 110px !important;
            padding: 16px 20px !important;
            text-align: left !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: flex-start !important;
            justify-content: center !important;
            background: linear-gradient(135deg, rgba(255,255,255,0.04), transparent) !important;
            border: 1px solid rgba(200, 164, 126, 0.2) !important;
            transition: all 0.2s ease !important;
        }
        .kpi-button button:hover {
            border-color: rgba(200, 164, 126, 0.6) !important;
            background: linear-gradient(135deg, rgba(200, 164, 126, 0.08), transparent) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(200, 164, 126, 0.2) !important;
        }
        .kpi-button button p {
            line-height: 1.3 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    def kpi_card_label(emoji, title, value, sub=""):
        """สร้าง label สำหรับปุ่ม KPI"""
        sub_html = f"\n\n_{sub}_" if sub else ""
        return f"{emoji} **{title}**\n\n# {value}{sub_html}"

    if is_adm:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("📝", "PO ทั้งหมด", len(pos)),
                          key="kpi_all", use_container_width=True):
                goto_po_list()
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("⏳", "กำลังดำเนินการ", len(pending)),
                          key="kpi_pending", use_container_width=True):
                goto_po_list("รอจัดซื้อดำเนินการ")
            st.markdown('</div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("✅", "เสร็จสิ้น", len(completed)),
                          key="kpi_done", use_container_width=True):
                goto_po_list("เสร็จสมบูรณ์")
            st.markdown('</div>', unsafe_allow_html=True)
        with m4:
            total_amt = sum(p.get('total', 0) for p in valid)
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("💰", "ยอดรวม", f"฿{total_amt:,.0f}"),
                          key="kpi_total", use_container_width=True):
                st.session_state['mode'] = 'reports'
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("📝", "PO ของฉัน", len(pos)),
                          key="kpi_my", use_container_width=True):
                goto_po_list()
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("⏳", "ดำเนินการ", len(pending)),
                          key="kpi_my_pending", use_container_width=True):
                goto_po_list("รอจัดซื้อดำเนินการ")
            st.markdown('</div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(kpi_card_label("✅", "เสร็จสิ้น", len(completed)),
                          key="kpi_my_done", use_container_width=True):
                goto_po_list("เสร็จสมบูรณ์")
            st.markdown('</div>', unsafe_allow_html=True)

    # Issue alert — คลิกได้
    if issues:
        if st.button(f"⚠️ มี PO ที่มีปัญหา **{len(issues)} ใบ** — คลิกเพื่อตรวจสอบ →",
                      key="alert_issues", use_container_width=True, type="primary"):
            goto_po_list("มีปัญหา")

    # Stock low alert (admin only) — คลิกได้
    if is_adm:
        low_stock = db.get_low_stock_equipment(threshold=10)
        if low_stock:
            names = ", ".join(e['name'] for e in low_stock[:5])
            if len(low_stock) > 5:
                names += f" และอีก {len(low_stock) - 5} รายการ"
            if st.button(f"📉 สต็อกต่ำ **{len(low_stock)} รายการ:** {names} — คลิกเพื่อจัดการ →",
                          key="alert_stock", use_container_width=True):
                st.session_state['mode'] = 'equipment'
                st.rerun()

    st.divider()

    # งานที่ต้องทำ
    today = date.today()
    if is_adm:
        action = [p for p in pos if p['status'] in
                  ('รอจัดซื้อดำเนินการ', 'มีปัญหา')]
        # เพิ่มที่เลยกำหนด
        action += [p for p in pos
                   if p.get('expected_date') and p['expected_date'] < today.isoformat()
                   and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]
    else:
        action = [p for p in pos if p['status'] in
                  ('รับของแล้ว', 'มีปัญหา')]
        # เพิ่มที่ใกล้ครบกำหนด
        action += [p for p in pos
                   if p.get('expected_date')
                   and today.isoformat() <= p['expected_date']
                   <= (today + timedelta(days=3)).isoformat()
                   and p['status'] in ('สั่งซื้อแล้ว', 'กำลังขนส่ง')]

    seen = set()
    action = [p for p in action if not (p['id'] in seen or seen.add(p['id']))]

    st.markdown("### 🔔 ที่ต้องดำเนินการ")
    if not action:
        st.success("🎉 ไม่มีงานค้าง")
    else:
        for po in action[:5]:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
                with c1:
                    st.markdown(f"**{po['po_number']}**")
                    show_status_badge(po['status'])
                with c2:
                    st.caption(f"📦 {len(po.get('items', []))} รายการ")
                    if po.get('purpose'):
                        st.caption(f"🎯 {po['purpose'][:60]}")
                with c3:
                    if po.get('expected_date'):
                        days = days_until(po['expected_date'])
                        if days is not None:
                            if days < 0:
                                st.markdown(
                                    f"<span style='color:#A32D2D;'>🚨 เลย {-days} วัน</span>",
                                    unsafe_allow_html=True,
                                )
                            elif days == 0:
                                st.caption("📅 วันนี้")
                            else:
                                st.caption(f"📅 อีก {days} วัน")
                    if is_adm and po.get('total'):
                        st.caption(f"💰 ฿{po['total']:,.2f}")
                with c4:
                    if st.button("ดู →", key=f"act_{po['id']}",
                                 use_container_width=True):
                        st.session_state['view_po_id'] = po['id']
                        st.session_state['mode'] = 'po_view'
                        st.rerun()

    st.divider()

    # ภาพรวมสถานะ
    st.markdown("### 📊 ภาพรวมสถานะ")
    status_count = {}
    for p in pos:
        status_count[p['status']] = status_count.get(p['status'], 0) + 1

    cols = st.columns(len(db.PO_STATUSES))
    for col, status in zip(cols, db.PO_STATUSES):
        with col:
            emoji = STATUS_EMOJI.get(status, '')
            count = status_count.get(status, 0)
            st.metric(f"{emoji} {status}", count)


# ==================================================================
# Page imports
# ==================================================================

from pages_po import (render_po_list, render_po_create, render_po_view,
                       render_pending_receipt)
from pages_admin import (render_equipment, render_reports,
                          render_users, render_notifications)


# ==================================================================
# Main
# ==================================================================

SESSION_TIMEOUT_MIN = 5  # auto logout หลังไม่ได้ใช้ 5 นาที


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
    # ลอง restore session — URL ก่อน (เร็วและเสถียรกว่า), cookie เป็น fallback
    restore_session_from_url()
    if not st.session_state.get('user'):
        restore_session_from_cookie()

    if not st.session_state.get('user'):
        login_page()
        return

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

    render_header()
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


if __name__ == "__main__":
    main()
