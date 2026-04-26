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
<meta name="color-scheme" content="light">
<style>
    /* ============================================ */
    /* Lab Parfumo Premium Theme — Steel Blue       */
    /* ============================================ */

    :root {
        --primary: #4A6FA5;
        --primary-dark: #3A5A8C;
        --primary-light: #A8C0E0;
        --primary-soft: rgba(74, 111, 165, 0.08);
        --bg-page: #FFFFFF;
        --bg-card: #F4F6FA;
        --bg-card-hover: rgba(74, 111, 165, 0.06);
        --border-soft: rgba(74, 111, 165, 0.18);
        --border-active: rgba(74, 111, 165, 0.5);
        --text-primary: #1F2937;
        --text-secondary: #6B7280;
        --text-muted: #9CA3AF;
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
        --shadow-blue: 0 4px 16px rgba(74, 111, 165, 0.2);
        --gold: #4A6FA5;
        --gold-dark: #3A5A8C;
        --gold-light: #A8C0E0;
        --gold-soft: rgba(74, 111, 165, 0.08);
        --shadow-gold: 0 4px 16px rgba(74, 111, 165, 0.2);
        color-scheme: light;
    }

    /* Force light backgrounds */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] {
        background-color: #FFFFFF;
        color: #1F2937;
    }

    /* Headings */
    h1, h2, h3 {
        color: #4A6FA5 !important;
        letter-spacing: 0.3px;
    }
    h1 {
        background: linear-gradient(135deg, #4A6FA5 0%, #A8C0E0 50%, #4A6FA5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600 !important;
    }

    /* Buttons — primary */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #4A6FA5 0%, #3A5A8C 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3A5A8C 0%, #4A6FA5 100%) !important;
        color: #FFFFFF !important;
        box-shadow: var(--shadow-blue) !important;
        transform: translateY(-1px);
    }

    /* Buttons — secondary (สีขาว text ดำ) */
    .stButton button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        color: #1F2937 !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="secondary"]:hover {
        background: #F4F6FA !important;
        border-color: #4A6FA5 !important;
        color: #4A6FA5 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #6B7280 !important; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #4A6FA5 !important;
        border-bottom-color: #4A6FA5 !important;
    }

    /* Metric */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #F4F6FA 0%, transparent 100%);
        border: 1px solid rgba(74, 111, 165, 0.18);
        border-radius: 12px;
        padding: 12px 16px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 26px !important;
        color: #4A6FA5 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #6B7280 !important;
        font-weight: 400 !important;
    }

    /* Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
    }

    /* ----- Brand Header ----- */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
    }
    .brand-logo {
        width: 40px; height: 40px;
        background: linear-gradient(135deg, #4A6FA5, #3A5A8C);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: white;
        box-shadow: var(--shadow-blue);
    }
    .brand-name {
        font-size: 20px;
        font-weight: 700;
        color: #4A6FA5;
        letter-spacing: -0.5px;
        line-height: 1;
    }

    /* Login splash */
    .login-splash {
        text-align: center;
        margin: 40px 0;
    }
    .login-logo {
        width: 80px; height: 80px;
        background: linear-gradient(135deg, #4A6FA5, #3A5A8C);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        color: white;
        margin: 0 auto 16px;
        box-shadow: var(--shadow-blue);
    }
    .login-title {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #4A6FA5 0%, #A8C0E0 50%, #4A6FA5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
    }
    .login-subtitle {
        font-size: 14px;
        color: #6B7280;
        letter-spacing: 0.5px;
    }

    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 40px 20px;
        background: #F4F6FA;
        border-radius: 12px;
        border: 1px dashed #D1D5DB;
    }
    .empty-icon {
        font-size: 48px;
        margin-bottom: 12px;
        opacity: 0.6;
    }
    .empty-title {
        color: #4A6FA5;
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .empty-text {
        color: #6B7280;
        font-size: 14px;
        max-width: 400px;
        margin: 0 auto 16px;
        line-height: 1.6;
    }

    /* Alerts */
    .alert {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* Mobile responsive */
    @media (max-width: 768px) {
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 16px !important; }
        div[data-testid="stMetricValue"] { font-size: 20px !important; }
        .stButton button {
            min-height: 44px !important;
            font-size: 14px !important;
        }
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

    # ===== Layout: Brand | Main Nav | Actions =====
    if is_admin():
        # admin: 4 main + 1 dropdown
        c1, c2, c3 = st.columns([2.5, 6, 1.8])
    else:
        c1, c2, c3 = st.columns([2.5, 5, 1.8])

    # ----- Brand -----
    with c1:
        st.markdown(f"""
        <div class="brand-header">
            <div class="brand-logo">📦</div>
            <div>
                <div class="brand-name">Lab Parfumo</div>
                <div style="font-size: 11px; color: rgba(255, 255, 255, 0.85); letter-spacing: 0.5px; margin-top: -2px;">
                    {emoji} {user['full_name']} • {role_label}
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

    # ===== Quick Stats — Insights แบบเร็ว =====
    if is_adm:
        try:
            from collections import Counter

            # คำนวณ insights
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

            this_total = sum(p.get('total_amount', 0) or 0 for p in this_month_pos)
            last_total = sum(p.get('total_amount', 0) or 0 for p in last_month_pos)
            growth = ((this_total - last_total) / last_total * 100) if last_total else 0

            # Top supplier
            supplier_amounts = {}
            for p in pos:
                if p.get('supplier_name') and p.get('total_amount'):
                    supplier_amounts[p['supplier_name']] = supplier_amounts.get(p['supplier_name'], 0) + p['total_amount']
            top_supplier = max(supplier_amounts.items(), key=lambda x: x[1]) if supplier_amounts else None
            total_amount_all = sum(supplier_amounts.values()) or 1
            top_pct = (top_supplier[1] / total_amount_all * 100) if top_supplier else 0

            # PO ค้างนานสุด
            today = datetime.now()
            longest_pending = None
            longest_days = 0
            for p in pos:
                if p['status'] in ('รอจัดซื้อดำเนินการ', 'สั่งซื้อแล้ว', 'กำลังขนส่ง'):
                    try:
                        created = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
                        days = (today - created).days
                        if days > longest_days:
                            longest_days = days
                            longest_pending = p
                    except Exception:
                        pass

            st.markdown("##### 💡 Quick Insights")
            qc1, qc2, qc3 = st.columns(3)
            with qc1:
                arrow = "📈" if growth > 0 else "📉" if growth < 0 else "➡️"
                color = "#1D9E75" if growth > 0 else "#A32D2D" if growth < 0 else "#888"
                st.markdown(
                    f'<div style="background:#F4F6FA; padding:14px 16px; '
                    f'border-radius:10px; border:1px solid rgba(74,111,165,0.15);">'
                    f'<div style="font-size:11px; color:#6B7280; '
                    f'text-transform:uppercase; letter-spacing:0.5px;">'
                    f'💰 ใช้จ่ายเดือนนี้</div>'
                    f'<div style="font-size:22px; font-weight:600; color:#4A6FA5; '
                    f'margin-top:4px;">฿{this_total:,.0f}</div>'
                    f'<div style="font-size:12px; color:{color}; margin-top:2px;">'
                    f'{arrow} {abs(growth):.0f}% จากเดือนที่แล้ว</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with qc2:
                if top_supplier:
                    name = top_supplier[0]
                    short_name = name if len(name) <= 20 else name[:18] + "…"
                    st.markdown(
                        f'<div style="background:#F4F6FA; padding:14px 16px; '
                        f'border-radius:10px; border:1px solid rgba(74,111,165,0.15);">'
                        f'<div style="font-size:11px; color:#6B7280; '
                        f'text-transform:uppercase; letter-spacing:0.5px;">'
                        f'🏆 Top Supplier</div>'
                        f'<div style="font-size:16px; font-weight:600; color:#4A6FA5; '
                        f'margin-top:4px;" title="{name}">{short_name}</div>'
                        f'<div style="font-size:12px; color:#6B7280; margin-top:2px;">'
                        f'{top_pct:.0f}% ของยอด • ฿{top_supplier[1]:,.0f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="background:#F4F6FA; padding:14px 16px; '
                        'border-radius:10px; border:1px solid rgba(74,111,165,0.15);">'
                        '<div style="font-size:11px; color:#6B7280;">🏆 Top Supplier</div>'
                        '<div style="font-size:14px; color:#9CA3AF; margin-top:8px;">'
                        'ยังไม่มีข้อมูล</div></div>',
                        unsafe_allow_html=True,
                    )
            with qc3:
                if longest_pending:
                    color = "#A32D2D" if longest_days > 14 else "#BA7517" if longest_days > 7 else "#4A6FA5"
                    st.markdown(
                        f'<div style="background:#F4F6FA; padding:14px 16px; '
                        f'border-radius:10px; border:1px solid rgba(74,111,165,0.15);">'
                        f'<div style="font-size:11px; color:#6B7280; '
                        f'text-transform:uppercase; letter-spacing:0.5px;">'
                        f'⏱️ PO ค้างนานสุด</div>'
                        f'<div style="font-size:22px; font-weight:600; color:{color}; '
                        f'margin-top:4px;">{longest_days} วัน</div>'
                        f'<div style="font-size:12px; color:#6B7280; margin-top:2px;">'
                        f'{longest_pending["po_number"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="background:#F4F6FA; padding:14px 16px; '
                        'border-radius:10px; border:1px solid rgba(74,111,165,0.15);">'
                        '<div style="font-size:11px; color:#6B7280;">⏱️ PO ค้างนานสุด</div>'
                        '<div style="font-size:14px; color:#1D9E75; margin-top:8px;">'
                        '🎉 ไม่มี PO ค้าง</div></div>',
                        unsafe_allow_html=True,
                    )
            st.markdown("<br/>", unsafe_allow_html=True)
        except Exception:
            pass

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
            border: 1px solid rgba(74, 111, 165, 0.2) !important;
            transition: all 0.2s ease !important;
        }
        .kpi-button button:hover {
            border-color: rgba(74, 111, 165, 0.6) !important;
            background: linear-gradient(135deg, rgba(74, 111, 165, 0.08), transparent) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(74, 111, 165, 0.2) !important;
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
                    if po.get('supplier_name'):
                        st.caption(f"🏭 {po['supplier_name'][:60]}")
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

    # ภาพรวมสถานะ — คลิกการ์ดเพื่อ filter ดูในรายการ
    st.markdown("### 📊 ภาพรวมสถานะ")
    st.caption("คลิกที่สถานะเพื่อดูรายการ PO")

    status_count = {}
    for p in pos:
        status_count[p['status']] = status_count.get(p['status'], 0) + 1

    # ใช้ CSS เดียวกับ KPI cards
    cols = st.columns(len(db.PO_STATUSES))
    for col, status in zip(cols, db.PO_STATUSES):
        with col:
            emoji = STATUS_EMOJI.get(status, '')
            count = status_count.get(status, 0)
            # ตัดชื่อสถานะให้สั้นถ้ายาว
            short_status = status if len(status) <= 12 else status[:11] + "…"
            st.markdown('<div class="kpi-button">', unsafe_allow_html=True)
            if st.button(
                f"{emoji} **{short_status}**\n\n# {count}",
                key=f"status_card_{status}",
                use_container_width=True,
                help=f"คลิกเพื่อดู PO สถานะ '{status}'",
            ):
                goto_po_list(status)
            st.markdown('</div>', unsafe_allow_html=True)


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
