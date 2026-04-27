"""helpers.py - shared utilities สำหรับทุก pages

⭐ UPDATED:
- เพิ่ม esc() สำหรับ HTML escape (anti-XSS)
- เพิ่ม timezone helpers (Bangkok time)
- เพิ่ม Status constants
- เพิ่ม config constants
"""
from datetime import datetime, date, timezone, timedelta
import html as _html
import logging

import streamlit as st


# ==================================================================
# Config (เก็บไว้ที่เดียว — import ที่อื่น)
# ==================================================================
SESSION_TIMEOUT_MIN = 60
SESSION_COOKIE_MAX_AGE_DAYS = 7
LOGIN_LOCKOUT_MINUTES = 15
LOGIN_MAX_ATTEMPTS = 5
PASSWORD_MIN_LENGTH = 8

BANGKOK_TZ = timezone(timedelta(hours=7))


# ==================================================================
# Logging setup (ใช้ทั้ง app)
# ==================================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
)
log = logging.getLogger("po_pro")


# ==================================================================
# HTML escape (anti-XSS) — IMPORTANT
# ==================================================================
def esc(s):
    """Escape string เพื่อใส่ใน HTML อย่างปลอดภัย
    ใช้ทุกครั้งที่นำ user input ไปใส่ใน f-string ที่ render เป็น HTML
    
    ตัวอย่าง:
        ❌ st.markdown(f"<div>{user_name}</div>", unsafe_allow_html=True)
        ✅ st.markdown(f"<div>{esc(user_name)}</div>", unsafe_allow_html=True)
    """
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)


def esc_attr(s):
    """Escape สำหรับใส่ใน HTML attribute (รวมเครื่องหมายคำพูด)"""
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)


# ==================================================================
# Date/time formatters
# ==================================================================
def fmt_date(d):
    if not d:
        return "-"
    if isinstance(d, str):
        try:
            return (datetime.fromisoformat(d.split('T')[0]).date()
                    if 'T' in d else date.fromisoformat(d)).strftime('%d/%m/%Y')
        except Exception:
            return d
    return d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d)


def fmt_dt(d):
    if not d:
        return "-"
    if isinstance(d, str):
        try:
            clean = d.replace('Z', '+00:00').split('+')[0]
            return datetime.fromisoformat(clean).strftime('%d/%m/%Y %H:%M')
        except Exception:
            return d
    return d.strftime('%d/%m/%Y %H:%M') if hasattr(d, 'strftime') else str(d)


def days_until(d_str):
    """คืนจำนวนวันถึงวันนั้น (ติดลบถ้าเลยแล้ว)"""
    if not d_str:
        return None
    try:
        if isinstance(d_str, str):
            d = (datetime.fromisoformat(d_str.split('T')[0]).date()
                 if 'T' in d_str else date.fromisoformat(d_str))
        else:
            d = d_str
        return (d - date.today()).days
    except Exception:
        return None


# ==================================================================
# Timezone helpers (Bangkok)
# ==================================================================
def now_bkk():
    """ปัจจุบันใน Bangkok time (timezone-aware)"""
    return datetime.now(BANGKOK_TZ)


def now_utc():
    """ปัจจุบันใน UTC (timezone-aware) — ใช้เก็บใน DB"""
    return datetime.now(timezone.utc)


def parse_iso_to_bkk(s):
    """แปลง ISO string เป็น Bangkok time"""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(BANGKOK_TZ)
    except Exception:
        return None


# ==================================================================
# User context helpers
# ==================================================================
def is_admin():
    u = st.session_state.get('user')
    return bool(u and u.get('role') == 'admin')


def current_user():
    return st.session_state.get('user') or {}


def uid():
    u = current_user()
    return u.get('id')


def uname():
    u = current_user()
    return u.get('full_name', '')


def urole():
    u = current_user()
    return u.get('role', 'requester')


# ==================================================================
# Status constants & helpers
# ==================================================================
class Status:
    """PO status constants — ใช้แทน magic strings"""
    PENDING = "รอจัดซื้อดำเนินการ"
    ORDERED = "สั่งซื้อแล้ว"
    SHIPPING = "กำลังขนส่ง"
    RECEIVED = "รับของแล้ว"
    PROBLEM = "มีปัญหา"
    COMPLETE = "เสร็จสมบูรณ์"
    CANCELLED = "ยกเลิก"

    ALL = (PENDING, ORDERED, SHIPPING, RECEIVED, PROBLEM, COMPLETE, CANCELLED)
    ACTIVE = (PENDING, ORDERED, SHIPPING)
    PENDING_RECEIPT = (ORDERED, SHIPPING)
    DONE = (COMPLETE, CANCELLED)
    NEEDS_RECEIPT = (RECEIVED, PROBLEM)


STATUS_COLOR = {
    Status.PENDING: "#888",
    Status.ORDERED: "#0F6E56",
    Status.SHIPPING: "#BA7517",
    Status.RECEIVED: "#1D9E75",
    Status.PROBLEM: "#A32D2D",
    Status.COMPLETE: "#27500A",
    Status.CANCELLED: "#A32D2D",
}

STATUS_EMOJI = {
    Status.PENDING: "📝",
    Status.ORDERED: "✅",
    Status.SHIPPING: "🚚",
    Status.RECEIVED: "📦",
    Status.PROBLEM: "⚠️",
    Status.COMPLETE: "✓",
    Status.CANCELLED: "❌",
}

STATUS_PILL_CLASS = {
    Status.PENDING: "pending",
    Status.ORDERED: "ordered",
    Status.SHIPPING: "shipping",
    Status.RECEIVED: "received",
    Status.PROBLEM: "problem",
    Status.COMPLETE: "done",
    Status.CANCELLED: "cancel",
}


def status_pill_html(status):
    """สร้าง HTML pill สำหรับ status (B2B style)
    ⭐ Status เป็น constant ที่ controlled แล้ว — escape ป้องกันไว้เผื่อ"""
    cls = STATUS_PILL_CLASS.get(status, "cancel")
    return f'<span class="lp-pill {cls}">{esc(status)}</span>'


def show_status_pill(status):
    """แสดง status pill (เรียก st.markdown ให้เลย)"""
    st.markdown(status_pill_html(status), unsafe_allow_html=True)


def show_status_badge(status):
    """Legacy — ใช้ pill แทน"""
    show_status_pill(status)


def days_indicator(d_str, status):
    """คืน HTML แสดงสถานะวันใกล้/เลยกำหนด หรือ None"""
    if not d_str:
        return None
    if status not in (Status.ORDERED, Status.SHIPPING):
        return None
    days = days_until(d_str)
    if days is None:
        return None
    if days < 0:
        return f'<span style="color:#A32D2D; font-weight:500;">🚨 เลย {-days} วัน</span>'
    elif days <= 3:
        return f'<span style="color:#BA7517; font-weight:500;">⏰ เหลือ {days} วัน</span>'
    else:
        return f'<span style="color:#666; font-size:11px;">📅 อีก {days} วัน</span>'


def show_empty_state(icon, title, text, button_label=None, button_action=None):
    """แสดง empty state สวยๆ — มีไอคอน + ข้อความ + ปุ่ม CTA (optional)
    button_action: tuple (mode, optional_extra_state_dict) สำหรับเปลี่ยนหน้า
    
    ⭐ UPDATED: escape user-controllable params"""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">{esc(icon)}</div>
        <div class="empty-title">{esc(title)}</div>
        <div class="empty-text">{esc(text)}</div>
    </div>
    """, unsafe_allow_html=True)

    if button_label and button_action:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button(button_label, type="primary", use_container_width=True,
                         key=f"empty_cta_{title}"):
                mode, *extra = button_action
                st.session_state['mode'] = mode
                if extra and isinstance(extra[0], dict):
                    for k, v in extra[0].items():
                        st.session_state[k] = v
                st.rerun()


# ==================================================================
# Money formatting
# ==================================================================
def fmt_money(amount, decimals=2):
    """Format ตัวเลขเป็นเงินบาท"""
    try:
        return f"฿{float(amount):,.{decimals}f}"
    except (TypeError, ValueError):
        return "฿0.00"


def safe_float(v, default=0.0):
    """แปลงเป็น float แบบปลอดภัย"""
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def safe_int(v, default=0):
    """แปลงเป็น int แบบปลอดภัย"""
    try:
        return int(float(v)) if v is not None else default
    except (TypeError, ValueError):
        return default
