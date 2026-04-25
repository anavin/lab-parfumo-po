"""helpers.py - shared utilities สำหรับทุก pages"""
from datetime import datetime, date

import streamlit as st


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


# Status helpers
STATUS_COLOR = {
    "รอจัดซื้อดำเนินการ": "#888",
    "สั่งซื้อแล้ว": "#0F6E56",
    "กำลังขนส่ง": "#BA7517",
    "รับของแล้ว": "#1D9E75",
    "มีปัญหา": "#A32D2D",
    "เสร็จสมบูรณ์": "#27500A",
    "ยกเลิก": "#A32D2D",
}

STATUS_EMOJI = {
    "รอจัดซื้อดำเนินการ": "📝",
    "สั่งซื้อแล้ว": "✅",
    "กำลังขนส่ง": "🚚",
    "รับของแล้ว": "📦",
    "มีปัญหา": "⚠️",
    "เสร็จสมบูรณ์": "✓",
    "ยกเลิก": "❌",
}


def show_status_badge(status):
    color = STATUS_COLOR.get(status, '#666')
    emoji = STATUS_EMOJI.get(status, '⚪')
    st.markdown(
        f'<span style="background:{color}22; color:{color}; '
        f'padding:3px 12px; border-radius:12px; font-size:12px; font-weight:500;">'
        f'{emoji} {status}</span>',
        unsafe_allow_html=True,
    )


def days_indicator(d_str, status):
    """คืน HTML แสดงสถานะวันใกล้/เลยกำหนด หรือ None"""
    if not d_str:
        return None
    if status not in ('สั่งซื้อแล้ว', 'กำลังขนส่ง'):
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
    button_action: tuple (mode, optional_extra_state_dict) สำหรับเปลี่ยนหน้า"""
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-icon">{icon}</div>
        <div class="empty-title">{title}</div>
        <div class="empty-text">{text}</div>
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
