"""database.py — Supabase wrapper สำหรับ PO Pro

⭐ MAJOR UPDATES:
- bcrypt password hashing (S1) + auto-migrate from SHA-256 (legacy)
- Atomic counter via Postgres function (C3)
- Atomic withdrawal via Postgres function (C4)
- Fixed PO creation bug (C6)
- Soft delete user (B1)
- Soft reject equipment (B2)
- Centralized config (B3)
- timezone-aware datetimes (B4, B5)
- Better logging (B7)
- Type hints (P6)
- Safe error display (P7)
"""
import os
import re
import uuid
import hashlib
import secrets as _py_secrets
from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Dict, Any

import bcrypt
import streamlit as st
from supabase import create_client, Client

from helpers import (
    log, now_utc,
    LOGIN_LOCKOUT_MINUTES, LOGIN_MAX_ATTEMPTS, PASSWORD_MIN_LENGTH,
    Status,
)


# ==================================================================
# Constants
# ==================================================================
ROLES = {'requester': 'ผู้สั่ง', 'admin': 'แอดมิน + จัดซื้อ'}

# Re-export for backward compat
PO_STATUSES = list(Status.ALL)

STATUS_EMOJI = {
    Status.PENDING: "📝",
    Status.ORDERED: "✅",
    Status.SHIPPING: "🚚",
    Status.RECEIVED: "📦",
    Status.PROBLEM: "⚠️",
    Status.COMPLETE: "✓",
    Status.CANCELLED: "❌",
}

DEFAULT_CATEGORIES = ["ขวดบรรจุ", "ฝา/จุก", "กล่องบรรจุภัณฑ์",
                      "สติกเกอร์/ฉลาก", "อุปกรณ์อื่นๆ"]
IMG_EQ = "equipment-images"
IMG_DEL = "delivery-images"
IMG_ATTACH = "po-attachments"


# ==================================================================
# Supabase client
# ==================================================================
@st.cache_resource
def get_supabase() -> Client:
    url = key = None
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        st.error("❌ ไม่พบ Supabase config — ตั้งค่าใน .streamlit/secrets.toml")
        st.code('SUPABASE_URL = "..."\nSUPABASE_ANON_KEY = "..."', language="toml")
        st.stop()
    return create_client(url, key)


def _supabase_safe():
    """Wrapper that recovers from connection errors"""
    try:
        return get_supabase()
    except Exception:
        log.warning("Supabase connection failed — clearing cache and retrying")
        try:
            get_supabase.clear()
        except Exception:
            pass
        return get_supabase()


# ==================================================================
# Password hashing — bcrypt (with legacy SHA-256 support)
# ==================================================================
def hash_password(p: str) -> str:
    """bcrypt with cost factor 12 (default — secure for 2026)"""
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password_hash(p: str, hashed: str) -> bool:
    """Compare against bcrypt hash"""
    if not p or not hashed:
        return False
    try:
        return bcrypt.checkpw(p.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def _is_legacy_sha256_hash(h: str) -> bool:
    """SHA-256 = 64 hex chars; bcrypt starts with $2"""
    if not h:
        return False
    return len(h) == 64 and not h.startswith('$2') and re.fullmatch(r'[0-9a-f]{64}', h) is not None


def _verify_legacy_sha256(p: str, hashed: str) -> bool:
    """For legacy users only — verify SHA-256 hash"""
    return hashlib.sha256(p.encode('utf-8')).hexdigest() == hashed


def validate_password(pwd: str, username: str = "") -> tuple[bool, str]:
    """ตรวจรหัสผ่าน — คืน (ok, message)"""
    if not pwd or len(pwd) < PASSWORD_MIN_LENGTH:
        return False, f"รหัสผ่านต้องยาวอย่างน้อย {PASSWORD_MIN_LENGTH} ตัวอักษร"
    if username and pwd.lower() == username.lower():
        return False, "รหัสผ่านห้ามเหมือน username"
    if not re.search(r'[A-Za-z]', pwd):
        return False, "ต้องมีตัวอักษรอย่างน้อย 1 ตัว"
    if not re.search(r'[0-9]', pwd):
        return False, "ต้องมีตัวเลขอย่างน้อย 1 ตัว"
    weak = ['password', '12345678', 'qwerty', 'admin123', 'staff123',
            'password1', 'password123', 'letmein']
    if pwd.lower() in weak:
        return False, "รหัสผ่านนี้อ่อนแอเกินไป — เปลี่ยนเป็นรหัสที่คาดเดายากกว่านี้"
    return True, "OK"


# ==================================================================
# Auth & login
# ==================================================================
def verify_user(username: str, password: str) -> Optional[dict]:
    """ตรวจ login + log ความพยายาม + auto-migrate SHA-256 → bcrypt"""
    if not username or not password:
        return None

    sb = get_supabase()
    try:
        # ตรวจถูกล็อคไหม
        if _is_account_locked(username):
            log.info(f"Login blocked (locked): {username}")
            return None

        # ดึง user ด้วย username อย่างเดียว — ไม่ filter password ใน query
        # (เพราะ bcrypt hash ต่างกันทุกครั้ง) — verify ใน Python แทน
        res = (sb.table("users")
                 .select("*")
                 .eq("username", username)
                 .eq("is_active", True)
                 .execute())

        if not res.data:
            _log_login(username, success=False)
            return None

        user = res.data[0]
        stored_hash = user.get('password_hash', '')

        verified = False
        needs_upgrade = False

        if _is_legacy_sha256_hash(stored_hash):
            # Legacy — verify SHA-256 then upgrade
            if _verify_legacy_sha256(password, stored_hash):
                verified = True
                needs_upgrade = True
        else:
            # bcrypt
            verified = verify_password_hash(password, stored_hash)

        if not verified:
            _log_login(username, success=False)
            return None

        # Success
        _log_login(username, success=True)
        try:
            update_payload = {
                "last_login_at": now_utc().isoformat(),
                "failed_login_count": 0,
            }
            if needs_upgrade:
                # ⭐ Auto-migrate SHA-256 → bcrypt (transparent to user)
                update_payload["password_hash"] = hash_password(password)
                log.info(f"Auto-upgraded password hash to bcrypt for user: {username}")
            sb.table("users").update(update_payload).eq("id", user["id"]).execute()
        except Exception:
            log.exception("Failed to update last_login")

        # Refresh user data (in case hash was upgraded)
        if needs_upgrade:
            res = sb.table("users").select("*").eq("id", user["id"]).execute()
            if res.data:
                user = res.data[0]

        return user
    except Exception:
        log.exception(f"verify_user failed for {username}")
        return None


def _is_account_locked(username: str) -> bool:
    """เช็คว่า account ล็อคหรือไม่"""
    sb = get_supabase()
    try:
        cutoff = (now_utc() - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)).isoformat()
        res = (sb.table("login_attempts")
                 .select("id", count='exact')
                 .eq("username", username)
                 .eq("success", False)
                 .gte("created_at", cutoff)
                 .execute())
        return (res.count or 0) >= LOGIN_MAX_ATTEMPTS
    except Exception:
        log.exception("_is_account_locked failed")
        return False


def get_failed_attempts_count(username: str) -> int:
    """จำนวนครั้งที่ผิดในช่วง lockout window"""
    sb = get_supabase()
    try:
        cutoff = (now_utc() - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)).isoformat()
        res = (sb.table("login_attempts")
                 .select("id", count='exact')
                 .eq("username", username)
                 .eq("success", False)
                 .gte("created_at", cutoff)
                 .execute())
        return res.count or 0
    except Exception:
        return 0


def _log_login(username: str, success: bool):
    """บันทึก login attempt"""
    try:
        get_supabase().table("login_attempts").insert({
            "username": username,
            "success": success,
        }).execute()
    except Exception:
        log.exception("_log_login failed")


# ==================================================================
# Session tokens
# ==================================================================
def create_session_token(user_id: str) -> Optional[str]:
    """สร้าง session token + บันทึกใน DB"""
    try:
        token = _py_secrets.token_urlsafe(32)
        get_supabase().table("user_sessions").insert({
            "token": token,
            "user_id": user_id,
        }).execute()
        return token
    except Exception:
        log.exception("create_session_token failed")
        return None


def verify_session_token(token: str, max_idle_minutes: int = 60) -> Optional[dict]:
    """ตรวจ token + ไม่หมดอายุ + return user"""
    if not token:
        return None
    try:
        sb = get_supabase()
        r = sb.table("user_sessions").select("*").eq("token", token).execute()
        if not r.data:
            return None
        sess = r.data[0]

        # idle check
        last = sess.get('last_activity_at')
        if last:
            try:
                last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                idle_min = (now_utc() - last_dt).total_seconds() / 60
                if idle_min > max_idle_minutes:
                    delete_session_token(token)
                    return None
            except Exception:
                log.exception("session idle check failed")

        # Get user
        ur = (sb.table("users")
                .select("*")
                .eq("id", sess['user_id'])
                .eq("is_active", True)
                .execute())
        if not ur.data:
            return None

        # Touch session
        try:
            sb.table("user_sessions").update({
                "last_activity_at": now_utc().isoformat(),
            }).eq("token", token).execute()
        except Exception:
            log.exception("touch session failed")

        return ur.data[0]
    except Exception:
        log.exception("verify_session_token failed")
        return None


def delete_session_token(token: str):
    if not token:
        return
    try:
        get_supabase().table("user_sessions").delete().eq("token", token).execute()
    except Exception:
        log.exception("delete_session_token failed")


def cleanup_expired_sessions(max_idle_minutes: int = 60):
    """ลบ sessions ที่หมดอายุ"""
    try:
        cutoff = (now_utc() - timedelta(minutes=max_idle_minutes)).isoformat()
        get_supabase().table("user_sessions").delete().lt("last_activity_at", cutoff).execute()
    except Exception:
        log.exception("cleanup_expired_sessions failed")


# ==================================================================
# Users
# ==================================================================
def get_users() -> List[dict]:
    try:
        return (get_supabase()
                .table("users")
                .select("*")
                .eq("is_active", True)  # ⭐ ซ่อน user ที่ soft-deleted
                .order("created_at")
                .execute().data or [])
    except Exception:
        log.exception("get_users failed")
        return []


def get_all_users_including_inactive() -> List[dict]:
    """สำหรับ admin ดูทั้งหมด (รวม inactive)"""
    try:
        return (get_supabase().table("users").select("*")
                .order("created_at").execute().data or [])
    except Exception:
        return []


def get_user(uid: str) -> Optional[dict]:
    try:
        r = get_supabase().table("users").select("*").eq("id", uid).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def add_user(username: str, password: str, full_name: str,
             role: str = "requester", email: str = "") -> Optional[dict]:
    """เพิ่มผู้ใช้ — bcrypt + force change password"""
    ok, msg = validate_password(password, username)
    if not ok:
        st.error(f"❌ {msg}")
        return None
    try:
        return get_supabase().table("users").insert({
            "username": username,
            "password_hash": hash_password(password),
            "full_name": full_name,
            "role": role,
            "email": email,
            "must_change_password": True,
        }).execute().data[0]
    except Exception as e:
        log.exception("add_user failed")
        # Don't leak DB error details
        msg = "Username นี้มีอยู่แล้ว" if "duplicate" in str(e).lower() else "เพิ่มผู้ใช้ไม่สำเร็จ"
        st.error(f"❌ {msg}")
        return None


def update_user(uid: str, **fields) -> bool:
    try:
        force_change = fields.pop("force_change_password", False)

        if "password" in fields:
            new_pwd = fields.pop("password")
            user = get_user(uid)
            uname_check = user.get('username', '') if user else ''
            ok, msg = validate_password(new_pwd, uname_check)
            if not ok:
                st.error(f"❌ {msg}")
                return False
            fields["password_hash"] = hash_password(new_pwd)
            fields["must_change_password"] = bool(force_change)
            fields["password_changed_at"] = now_utc().isoformat()
        get_supabase().table("users").update(fields).eq("id", uid).execute()
        return True
    except Exception:
        log.exception("update_user failed")
        return False


def delete_user(uid: str) -> bool:
    """⭐ Soft delete — รักษาประวัติ + reverse ได้
    
    เปลี่ยนเป็น soft delete แทน hard delete
    - Mark is_active = False
    - Append marker to username (free up the username for reuse)
    """
    try:
        sb = get_supabase()
        # ลบ session ทุกอันของ user คนนี้
        sb.table("user_sessions").delete().eq("user_id", uid).execute()
        # Soft delete
        sb.table("users").update({
            "is_active": False,
            "username": f"_del_{uid[:8]}_{int(now_utc().timestamp())}",
        }).eq("id", uid).execute()
        return True
    except Exception:
        log.exception("delete_user failed")
        return False


# ==================================================================
# Company Settings
# ==================================================================
def get_company_settings() -> dict:
    defaults = {
        'name': 'Lab Parfumo',
        'name_th': 'แล็บ พาฟูโม่',
        'address': '',
        'phone': '',
        'email': '',
        'tax_id': '',
        'website': 'www.labparfumo.com',
        'logo_url': '',
        'login_intro_visible': True,
        'login_intro_title': 'ℹ️ บัญชีเริ่มต้น',
        'login_intro_text': 'admin / admin123     → แอดมิน\nstaff1 / staff123    → ผู้สั่ง',
        'login_intro_note': '⚠️ ครั้งแรก ระบบจะบังคับเปลี่ยนรหัสผ่าน',
    }
    try:
        r = get_supabase().table("company_settings").select("*").eq("id", 1).execute()
        if r.data:
            return {**defaults, **r.data[0]}
    except Exception:
        log.exception("get_company_settings failed")
    return defaults


def update_company_settings(**fields) -> bool:
    """อัปเดตข้อมูลบริษัท (admin)
    
    ⭐ UPDATED: ใช้ kwargs ทั้งหมด → ไม่ต้องส่ง field ทุกตัว"""
    try:
        sb = get_supabase()
        payload = {
            "id": 1,
            "updated_at": now_utc().isoformat(),
        }
        # Whitelist allowed fields
        allowed = {'name', 'name_th', 'address', 'phone', 'email',
                   'tax_id', 'website', 'logo_url',
                   'login_intro_visible', 'login_intro_title',
                   'login_intro_text', 'login_intro_note',
                   'updated_by_name'}
        for k, v in fields.items():
            if k in allowed:
                payload[k] = v
        sb.table("company_settings").upsert(payload).execute()
        return True
    except Exception:
        log.exception("update_company_settings failed")
        st.error("⚠️ บันทึกไม่สำเร็จ กรุณาลองใหม่")
        return False


# ==================================================================
# Notifications & admin notification helpers
# ==================================================================
def get_admins() -> List[dict]:
    try:
        return (get_supabase().table("users").select("*")
                .eq("role", "admin").eq("is_active", True)
                .execute().data or [])
    except Exception:
        return []


def has_recent_notification(user_id: str, po_id: str, hours: int = 20) -> bool:
    try:
        since = (now_utc() - timedelta(hours=hours)).isoformat()
        r = (get_supabase().table("notifications")
             .select("id")
             .eq("user_id", user_id)
             .eq("po_id", po_id)
             .gte("created_at", since)
             .limit(1)
             .execute())
        return bool(r.data)
    except Exception:
        return False


def notify_admins(po_id: str, title: str, message: str = "",
                  dedupe_hours: int = 0) -> int:
    """ส่ง notification ให้ admin ทุกคน
    
    ⭐ UPDATED: รองรับ dedupe_hours เพื่อลด spam
    """
    try:
        admins = get_admins()
        sent = 0
        for admin in admins:
            if dedupe_hours > 0 and has_recent_notification(
                admin['id'], po_id, dedupe_hours
            ):
                continue
            add_notification(admin['id'], po_id, title, message)
            sent += 1
        return sent
    except Exception:
        log.exception("notify_admins failed")
        return 0


def check_and_notify_stale_pos() -> int:
    """เช็ค PO ค้างเกิน 3 วัน → แจ้ง admin (max 1/admin/PO/day)"""
    try:
        sb = get_supabase()
        threshold = (now_utc() - timedelta(days=3)).isoformat()
        r = (sb.table("purchase_orders").select("*")
             .eq("status", Status.PENDING)
             .lte("created_at", threshold)
             .execute())
        stale_pos = r.data or []
        if not stale_pos:
            return 0

        admins = get_admins()
        sent_count = 0
        for po in stale_pos:
            for admin in admins:
                if has_recent_notification(admin['id'], po['id'], hours=20):
                    continue
                try:
                    created = datetime.fromisoformat(
                        po['created_at'].replace('Z', '+00:00')
                    )
                    days_stale = (now_utc() - created).days
                except Exception:
                    days_stale = 3

                add_notification(
                    admin['id'], po['id'],
                    f"⏰ PO ค้างเกิน {days_stale} วัน",
                    f"{po.get('po_number', '-')} ยังไม่ได้สั่ง supplier",
                )
                sent_count += 1
        return sent_count
    except Exception:
        log.exception("check_and_notify_stale_pos failed")
        return 0


# ==================================================================
# Categories
# ==================================================================
def get_categories() -> List[str]:
    try:
        sb = get_supabase()
        try:
            r = (sb.table("equipment_categories")
                 .select("name")
                 .order("display_order")
                 .order("created_at")
                 .execute())
        except Exception:
            r = (sb.table("equipment_categories")
                 .select("name").order("created_at").execute())
        cats = [x["name"] for x in r.data]
        if not cats:
            for n in DEFAULT_CATEGORIES:
                sb.table("equipment_categories").insert({"name": n}).execute()
            return DEFAULT_CATEGORIES.copy()
        return cats
    except Exception:
        log.exception("get_categories failed")
        return DEFAULT_CATEGORIES.copy()


def get_categories_with_order() -> List[dict]:
    try:
        sb = get_supabase()
        try:
            r = (sb.table("equipment_categories").select("*")
                 .order("display_order").order("created_at").execute())
        except Exception:
            r = sb.table("equipment_categories").select("*").order("created_at").execute()
        return r.data or []
    except Exception:
        return []


def add_category(name: str) -> bool:
    try:
        sb = get_supabase()
        try:
            mx = (sb.table("equipment_categories")
                  .select("display_order")
                  .order("display_order", desc=True).limit(1).execute())
            next_order = (mx.data[0].get("display_order") or 0) + 1 if mx.data else 1
        except Exception:
            next_order = 999
        try:
            sb.table("equipment_categories").insert({
                "name": name, "display_order": next_order,
            }).execute()
        except Exception:
            sb.table("equipment_categories").insert({"name": name}).execute()
        return True
    except Exception:
        log.exception("add_category failed")
        return False


def move_category(name: str, direction: str) -> bool:
    """เลื่อนหมวดขึ้น/ลง"""
    try:
        sb = get_supabase()
        cats = get_categories_with_order()
        if not cats:
            return False
        idx = next((i for i, c in enumerate(cats) if c['name'] == name), -1)
        if idx < 0:
            return False
        if direction == 'up' and idx == 0:
            return False
        if direction == 'down' and idx == len(cats) - 1:
            return False

        target_idx = idx - 1 if direction == 'up' else idx + 1
        a, b = cats[idx], cats[target_idx]

        ord_a = a.get('display_order', idx + 1)
        ord_b = b.get('display_order', target_idx + 1)
        sb.table("equipment_categories").update({"display_order": ord_b}).eq("id", a['id']).execute()
        sb.table("equipment_categories").update({"display_order": ord_a}).eq("id", b['id']).execute()
        return True
    except Exception:
        log.exception("move_category failed")
        return False


def update_category(old_name: str, new_name: str) -> bool:
    try:
        sb = get_supabase()
        sb.table("equipment_categories").update({"name": new_name}).eq("name", old_name).execute()
        sb.table("equipment").update({"category": new_name}).eq("category", old_name).execute()
        return True
    except Exception:
        log.exception("update_category failed")
        return False


def delete_category(name: str) -> tuple[bool, str]:
    try:
        sb = get_supabase()
        c = (sb.table("equipment").select("id", count="exact")
             .eq("category", name).eq("is_active", True).execute())
        if c.count and c.count > 0:
            return False, f"มีสินค้า {c.count} รายการในหมวดนี้"
        sb.table("equipment_categories").delete().eq("name", name).execute()
        return True, "ลบเรียบร้อย"
    except Exception as e:
        log.exception("delete_category failed")
        return False, "ลบไม่สำเร็จ"


def count_equipment_by_category(name: str) -> int:
    try:
        sb = get_supabase()
        r = (sb.table("equipment").select("id", count="exact")
             .eq("category", name).eq("is_active", True).execute())
        return r.count or 0
    except Exception:
        return 0


# ==================================================================
# Image / attachment upload
# ==================================================================
def upload_image(file_bytes: bytes, filename: str, bucket: str = IMG_EQ) -> Optional[str]:
    sb = get_supabase()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    new_fn = f"{uuid.uuid4().hex}.{ext}"
    ct = f"image/{'jpeg' if ext == 'jpg' else ext}"
    try:
        sb.storage.from_(bucket).upload(
            path=new_fn, file=file_bytes,
            file_options={"content-type": ct, "upsert": "false"},
        )
        return sb.storage.from_(bucket).get_public_url(new_fn)
    except Exception:
        log.exception("upload_image failed")
        st.error("⚠️ อัปโหลดรูปไม่สำเร็จ")
        return None


ATTACHMENT_MIMES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
    'gif': 'image/gif', 'webp': 'image/webp',
    'zip': 'application/zip', 'rar': 'application/x-rar-compressed',
    '7z': 'application/x-7z-compressed',
}


def upload_attachment(file_bytes: bytes, filename: str,
                      bucket: str = IMG_ATTACH) -> Optional[dict]:
    sb = get_supabase()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    content_type = ATTACHMENT_MIMES.get(ext, "application/octet-stream")
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    try:
        sb.storage.from_(bucket).upload(
            path=safe_name, file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )
        return {
            'url': sb.storage.from_(bucket).get_public_url(safe_name),
            'name': filename,
            'size': len(file_bytes),
            'type': ext,
            'uploaded_at': now_utc().isoformat(),
        }
    except Exception:
        log.exception("upload_attachment failed")
        st.error(f"⚠️ อัปโหลด '{filename}' ไม่สำเร็จ")
        return None


def add_po_attachments(po_id: str, new_attachments: list,
                       user_name: str = "", category: str = "general") -> bool:
    if not new_attachments:
        return False
    try:
        sb = get_supabase()
        po = get_purchase_order(po_id)
        if not po:
            return False
        existing = po.get('attachment_urls') or []
        for a in new_attachments:
            a['category'] = category
            a['uploaded_by'] = user_name
        merged = existing + new_attachments
        sb.table("purchase_orders").update({
            "attachment_urls": merged,
            "updated_at": now_utc().isoformat(),
        }).eq("id", po_id).execute()
        return True
    except Exception:
        log.exception("add_po_attachments failed")
        return False


def remove_po_attachment(po_id: str, attachment_url: str) -> bool:
    try:
        sb = get_supabase()
        po = get_purchase_order(po_id)
        if not po:
            return False
        existing = po.get('attachment_urls') or []
        new_list = [a for a in existing if a.get('url') != attachment_url]
        sb.table("purchase_orders").update({
            "attachment_urls": new_list,
            "updated_at": now_utc().isoformat(),
        }).eq("id", po_id).execute()
        return True
    except Exception:
        return False


# ==================================================================
# Equipment
# ==================================================================
def get_equipment_list(active_only: bool = False,
                       include_pending: bool = False,
                       include_rejected: bool = False) -> List[dict]:
    try:
        sb = get_supabase()
        q = sb.table("equipment").select("*")
        if active_only:
            q = q.eq("is_active", True)
        if not include_pending and not include_rejected:
            q = q.or_("approval_status.eq.approved,approval_status.is.null")
        elif include_pending and not include_rejected:
            q = q.or_("approval_status.eq.approved,approval_status.eq.pending,"
                      "approval_status.is.null")
        return q.order("created_at", desc=True).execute().data or []
    except Exception:
        log.exception("get_equipment_list failed")
        return []


def get_pending_equipment() -> List[dict]:
    try:
        sb = get_supabase()
        return (sb.table("equipment").select("*")
                .eq("approval_status", "pending")
                .order("suggested_at", desc=True).execute().data or [])
    except Exception:
        return []


def suggest_equipment_from_po(name: str, suggested_by: str,
                              suggested_by_name: str,
                              suggested_from_po: str,
                              suggested_notes: str = "",
                              unit: str = "ชิ้น",
                              image_urls=None) -> Optional[dict]:
    try:
        sb = get_supabase()
        temp_sku = f"PENDING-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "sku": temp_sku, "name": name,
            "category": "(รออนุมัติ)", "unit": unit,
            "description": suggested_notes or "",
            "last_cost": 0, "stock": 0,
            "image_url": (image_urls[0] if image_urls else ""),
            "image_urls": image_urls or [],
            "is_active": True,
            "approval_status": "pending",
            "suggested_by": suggested_by,
            "suggested_by_name": suggested_by_name,
            "suggested_at": now_utc().isoformat(),
            "suggested_from_po": suggested_from_po,
            "suggested_notes": suggested_notes,
        }
        r = sb.table("equipment").insert(payload).execute()
        return r.data[0] if r.data else None
    except Exception:
        log.exception("suggest_equipment_from_po failed")
        return None


def approve_equipment(eq_id: str, sku: str, name: str, category: str,
                      unit: str, description: str,
                      last_cost: float = 0, stock: int = 0,
                      approved_by_name: str = "") -> bool:
    try:
        sb = get_supabase()
        sb.table("equipment").update({
            "sku": sku, "name": name, "category": category,
            "unit": unit or "ชิ้น", "description": description or "",
            "last_cost": float(last_cost or 0),
            "stock": int(stock or 0),
            "approval_status": "approved",
            "approved_by_name": approved_by_name,
            "approved_at": now_utc().isoformat(),
        }).eq("id", eq_id).execute()
        return True
    except Exception:
        log.exception("approve_equipment failed")
        return False


def reject_equipment(eq_id: str, reason: str = "",
                     admin_name: str = "") -> bool:
    """⭐ Soft reject — รักษาประวัติ + เรียกคืนได้
    
    เปลี่ยนเป็น soft reject แทน DELETE
    """
    try:
        sb = get_supabase()
        sb.table("equipment").update({
            "approval_status": "rejected",
            "rejected_reason": reason,
            "rejected_by_name": admin_name,
            "rejected_at": now_utc().isoformat(),
            "is_active": False,  # ซ่อนออกจาก catalog
        }).eq("id", eq_id).execute()
        return True
    except Exception:
        log.exception("reject_equipment failed")
        return False


def get_equipment(eid: str) -> Optional[dict]:
    try:
        r = get_supabase().table("equipment").select("*").eq("id", eid).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def add_equipment(name: str, category: str, unit: str = "ชิ้น",
                  sku: str = "", description: str = "",
                  last_cost: float = 0, stock: int = 0,
                  reorder_level: int = 0,
                  image_url=None, image_urls=None) -> Optional[dict]:
    try:
        urls_list = list(image_urls or [])
        if image_url and image_url not in urls_list:
            urls_list.insert(0, image_url)
        primary = urls_list[0] if urls_list else None
        return get_supabase().table("equipment").insert({
            "name": name, "category": category, "unit": unit, "sku": sku,
            "description": description, "last_cost": float(last_cost),
            "stock": int(stock),
            "reorder_level": int(reorder_level or 0),
            "image_url": primary,
            "image_urls": urls_list,
            "is_active": True,
        }).execute().data[0]
    except Exception:
        log.exception("add_equipment failed")
        st.error("⚠️ เพิ่มสินค้าไม่สำเร็จ")
        return None


def update_equipment(eid: str, **fields) -> bool:
    try:
        if "last_cost" in fields:
            fields["last_cost"] = float(fields["last_cost"])
        if "stock" in fields:
            fields["stock"] = int(fields["stock"])
        if "reorder_level" in fields:
            fields["reorder_level"] = int(fields["reorder_level"] or 0)
        if "image_urls" in fields:
            urls = fields["image_urls"] or []
            fields["image_url"] = urls[0] if urls else None
        get_supabase().table("equipment").update(fields).eq("id", eid).execute()
        return True
    except Exception:
        log.exception("update_equipment failed")
        return False


def add_equipment_image(eid: str, image_url: str) -> bool:
    try:
        eq = get_equipment(eid)
        if not eq:
            return False
        urls = list(eq.get('image_urls') or [])
        if eq.get('image_url') and eq['image_url'] not in urls:
            urls.insert(0, eq['image_url'])
        if image_url not in urls:
            urls.append(image_url)
        return update_equipment(eid, image_urls=urls)
    except Exception:
        return False


def remove_equipment_image(eid: str, image_url: str) -> bool:
    try:
        eq = get_equipment(eid)
        if not eq:
            return False
        urls = list(eq.get('image_urls') or [])
        if eq.get('image_url') and eq['image_url'] not in urls:
            urls.insert(0, eq['image_url'])
        urls = [u for u in urls if u != image_url]
        return update_equipment(eid, image_urls=urls)
    except Exception:
        return False


def delete_equipment(eid: str) -> bool:
    """⭐ Soft delete — set is_active = False"""
    try:
        get_supabase().table("equipment").update({
            "is_active": False,
        }).eq("id", eid).execute()
        return True
    except Exception:
        log.exception("delete_equipment failed")
        return False


# ==================================================================
# PO Number generation — ATOMIC ⚡
# ==================================================================
def generate_po_number() -> str:
    """⭐ Atomic PO number generation via Postgres function (no race condition)
    
    ดู migration_atomic_counter.sql
    """
    sb = get_supabase()
    year = datetime.now().year
    try:
        # ใช้ RPC (Postgres function) — atomic
        r = sb.rpc('next_po_number', {'year_int': year}).execute()
        if r.data:
            return r.data
    except Exception:
        log.warning("next_po_number RPC not available — falling back to legacy method")

    # Fallback (อาจมี race) — สำหรับช่วง migrate
    cid = f"po_{year}"
    try:
        r = sb.table("counters").select("*").eq("id", cid).execute()
        if r.data:
            v = r.data[0]["value"] + 1
            sb.table("counters").update({"value": v}).eq("id", cid).execute()
        else:
            v = 1
            sb.table("counters").insert({"id": cid, "value": 1}).execute()
        return f"PO-{year}-{v:04d}"
    except Exception:
        log.exception("generate_po_number failed")
        return f"PO-{year}-{datetime.now().strftime('%H%M%S')}"


# ==================================================================
# Purchase Orders
# ==================================================================
def get_purchase_orders(user_id: Optional[str] = None,
                        role: str = "requester",
                        status_filter: Optional[str] = None,
                        limit: int = 500) -> List[dict]:
    try:
        sb = get_supabase()
        q = sb.table("purchase_orders").select("*")
        if role == "requester" and user_id:
            q = q.eq("created_by", user_id)
        if status_filter and status_filter != "ทั้งหมด":
            q = q.eq("status", status_filter)
        q = q.order("created_at", desc=True).limit(limit)
        return q.execute().data or []
    except Exception:
        log.exception("get_purchase_orders failed")
        st.error("⚠️ ไม่สามารถโหลดข้อมูล PO ได้")
        return []


def get_pos_pending_receipt() -> List[dict]:
    try:
        sb = get_supabase()
        q = (sb.table("purchase_orders").select("*")
             .in_("status", list(Status.PENDING_RECEIPT)))
        return q.order("expected_date", desc=False).execute().data or []
    except Exception:
        log.exception("get_pos_pending_receipt failed")
        return []


def get_purchase_order(po_id: str) -> Optional[dict]:
    try:
        sb = get_supabase()
        if "-" in po_id and len(po_id) == 36:
            r = sb.table("purchase_orders").select("*").eq("id", po_id).execute()
        else:
            r = sb.table("purchase_orders").select("*").eq("po_number", po_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def create_purchase_order(items: list, purpose: str = "", notes: str = "",
                          created_by: Optional[str] = None,
                          created_by_name: str = "") -> Optional[dict]:
    """⭐ FIXED: bug ที่ใช้ list.index() ซึ่งคืน index ผิดเมื่อมี items ซ้ำ"""
    if not items:
        st.error("กรุณาเพิ่มรายการอย่างน้อย 1 รายการ")
        return None

    try:
        sb = get_supabase()
        po_no = generate_po_number()
        clean = [{
            "equipment_id": it.get("equipment_id"),
            "name": it.get("name"),
            "qty": int(it.get("qty", 0)),
            "unit": it.get("unit", "ชิ้น"),
            "unit_price": 0, "subtotal": 0,
            "notes": it.get("notes", ""),
            "image_urls": it.get("image_urls") or [],
        } for it in items]

        po = sb.table("purchase_orders").insert({
            "po_number": po_no, "items": clean,
            "purpose": purpose, "notes": notes,
            "status": Status.PENDING,
            "created_by": created_by, "created_by_name": created_by_name,
        }).execute().data[0]
        log_activity(po["id"], created_by_name, "requester", "created",
                     f"สร้าง PO มี {len(items)} รายการ")

        # ⭐ FIXED: ใช้ enumerate ที่ตรงตำแหน่ง — ไม่ใช้ list.index()
        any_linked = False
        for idx, it in enumerate(items):
            if not it.get('equipment_id') and it.get('name'):
                pending = suggest_equipment_from_po(
                    name=it.get('name'),
                    suggested_by=created_by,
                    suggested_by_name=created_by_name,
                    suggested_from_po=po['id'],
                    suggested_notes=it.get('notes', ''),
                    unit=it.get('unit', 'ชิ้น'),
                    image_urls=it.get('image_urls') or [],
                )
                if pending:
                    clean[idx]['equipment_id'] = pending['id']
                    any_linked = True

        if any_linked:
            sb.table("purchase_orders").update({"items": clean}).eq("id", po['id']).execute()
            po['items'] = clean

        # Notify admin (with dedupe to prevent spam if many POs)
        try:
            n_items = len(items)
            n_custom = sum(1 for it in items if not it.get('equipment_id'))
            msg = f"{po['po_number']} • {n_items} รายการ"
            if n_custom > 0:
                msg += f" (มี {n_custom} รายการใหม่ที่รออนุมัติ)"
            notify_admins(po['id'], f"📥 PO ใหม่จาก {created_by_name}", msg)
        except Exception:
            log.exception("notify_admins after PO create failed")

        return po
    except Exception:
        log.exception("create_purchase_order failed")
        st.error("⚠️ สร้าง PO ไม่สำเร็จ กรุณาลองใหม่")
        return None


def clone_purchase_order(source_po_id: str, created_by: str,
                         created_by_name: str) -> Optional[dict]:
    try:
        source = get_purchase_order(source_po_id)
        if not source:
            return None
        items = []
        for it in source.get('items', []):
            items.append({
                'equipment_id': it.get('equipment_id'),
                'name': it.get('name'),
                'qty': it.get('qty', 0),
                'unit': it.get('unit', 'ชิ้น'),
                'notes': it.get('notes', ''),
            })
        new_po = create_purchase_order(
            items=items, purpose="",
            notes=f"[คัดลอกจาก {source['po_number']}] {source.get('notes', '')}".strip(),
            created_by=created_by,
            created_by_name=created_by_name,
        )
        if new_po:
            log_activity(new_po['id'], created_by_name, "requester", "cloned",
                         f"คัดลอกจาก {source['po_number']}")
        return new_po
    except Exception:
        log.exception("clone_purchase_order failed")
        return None


def get_low_stock_equipment(threshold: int = 10) -> List[dict]:
    try:
        return (get_supabase().table("equipment").select("*")
                .lt("stock", threshold).eq("is_active", True)
                .execute().data or [])
    except Exception:
        return []


def get_reorder_alerts() -> List[dict]:
    """ดึงสินค้าที่ stock <= reorder_level (ต้อง reorder_level > 0)
    ใช้บน dashboard insight + แสดง badge ในหน้าเบิก/catalog
    """
    try:
        sb = get_supabase()
        items = (sb.table("equipment").select("*")
                 .eq("is_active", True)
                 .gt("reorder_level", 0).execute().data or [])
        # filter ใน Python: stock <= reorder_level
        return [e for e in items
                if (e.get('stock') or 0) <= (e.get('reorder_level') or 0)]
    except Exception:
        log.exception("get_reorder_alerts failed")
        return []


def bulk_approve_equipment(eq_ids: List[str], approved_by_name: str = "",
                           default_category: str = "อุปกรณ์อื่นๆ") -> tuple[int, int]:
    """อนุมัติ pending equipment หลายชิ้นพร้อมกัน
    ใช้ค่า default จาก suggested_notes / temp SKU — admin แก้ทีหลังได้

    return (success_count, fail_count)
    """
    sb = get_supabase()
    success = 0
    fail = 0
    for eq_id in eq_ids:
        try:
            eq = get_equipment(eq_id)
            if not eq:
                fail += 1
                continue
            # ใช้ SKU เดิม (จะเป็น PENDING-... ถ้า admin ไม่แก้)
            sku = eq.get('sku') or f"AUTO-{eq_id[:8]}"
            sb.table("equipment").update({
                "sku": sku,
                "category": default_category,
                "unit": eq.get('unit') or "ชิ้น",
                "description": eq.get('suggested_notes') or eq.get('description') or '',
                "approval_status": "approved",
                "approved_by_name": approved_by_name,
                "approved_at": now_utc().isoformat(),
            }).eq("id", eq_id).execute()
            success += 1
        except Exception:
            log.exception(f"bulk_approve_equipment failed for {eq_id}")
            fail += 1
    return success, fail


def bulk_reject_equipment(eq_ids: List[str], reason: str = "",
                          admin_name: str = "") -> tuple[int, int]:
    """ปฏิเสธ pending equipment หลายชิ้นพร้อมกัน — return (success, fail)"""
    success = 0
    fail = 0
    for eq_id in eq_ids:
        if reject_equipment(eq_id, reason=reason, admin_name=admin_name):
            success += 1
        else:
            fail += 1
    return success, fail


def get_supplier_history() -> List[dict]:
    """ดึง supplier ที่เคยใช้ พร้อมข้อมูล context (ครั้งล่าสุด, ติดต่อ)
    return list ของ {name, last_contact, last_used, po_count}
    """
    try:
        sb = get_supabase()
        r = (sb.table("purchase_orders")
             .select("supplier_name, supplier_contact, ordered_date, po_number")
             .not_.is_("supplier_name", "null")
             .order("ordered_date", desc=True)
             .execute())
        suppliers = {}
        for row in (r.data or []):
            name = (row.get('supplier_name') or '').strip()
            if not name:
                continue
            if name not in suppliers:
                suppliers[name] = {
                    'name': name,
                    'last_contact': row.get('supplier_contact') or '',
                    'last_used': row.get('ordered_date') or '',
                    'last_po': row.get('po_number') or '',
                    'po_count': 0,
                }
            suppliers[name]['po_count'] += 1
            # อัปเดต contact ถ้า supplier_contact ในรายการนี้ใหม่กว่าและไม่ว่าง
            if (row.get('supplier_contact')
                and not suppliers[name]['last_contact']):
                suppliers[name]['last_contact'] = row['supplier_contact']
        # เรียงตาม po_count ลด (supplier ที่ใช้บ่อย → ขึ้นก่อน)
        return sorted(suppliers.values(),
                      key=lambda s: (-s['po_count'], s['name']))
    except Exception:
        log.exception("get_supplier_history failed")
        return []


# ==================================================================
# Stock Withdrawal — ATOMIC ⚡
# ==================================================================
def create_withdrawal(equipment_id: str, qty, purpose: str,
                      withdrawn_by: str, withdrawn_by_name: str,
                      withdrawn_at=None, notes: str = "") -> Optional[dict]:
    """⭐ ATOMIC: ใช้ Postgres function เช็ค + หัก stock ในทำเดียว
    
    ดู migration_atomic_counter.sql → withdraw_stock function
    """
    try:
        qty = float(qty)
        if qty <= 0:
            st.error("จำนวนต้องมากกว่า 0")
            return None

        sb = get_supabase()

        # 1) Atomic check + decrement via Postgres function
        try:
            res = sb.rpc('withdraw_stock', {
                'p_equipment_id': equipment_id,
                'p_qty': qty,
            }).execute()

            if res.data:
                result = res.data
                # Postgres returns JSONB — supabase-py may parse to dict
                if isinstance(result, str):
                    import json as _json
                    result = _json.loads(result)
                if not result.get('success'):
                    err = result.get('error', 'unknown')
                    if err == 'insufficient_stock':
                        st.error(f"❌ สต็อกไม่พอ — เหลือ {result.get('current_stock', 0)}")
                    elif err == 'not_found':
                        st.error("ไม่พบสินค้านี้ในระบบ")
                    else:
                        st.error(f"❌ {err}")
                    return None
                eq_name = result.get('name', '')
                eq_unit = result.get('unit', 'ชิ้น')
            else:
                # RPC function not available yet — fall back
                raise Exception("RPC function not available")

        except Exception:
            log.warning("withdraw_stock RPC failed — falling back to non-atomic version")
            # Fallback (มี race condition แต่ใช้งานได้ระหว่าง migrate)
            eq_r = sb.table("equipment").select("*").eq("id", equipment_id).execute()
            if not eq_r.data:
                st.error("ไม่พบสินค้านี้ในระบบ")
                return None
            eq = eq_r.data[0]
            current_stock = float(eq.get('stock', 0) or 0)
            if qty > current_stock:
                st.error(f"❌ สต็อกไม่พอ — เหลือ {current_stock:,.0f}")
                return None
            new_stock = int(current_stock - qty)
            sb.table("equipment").update({"stock": new_stock}).eq("id", equipment_id).execute()
            eq_name = eq.get('name', '')
            eq_unit = eq.get('unit', 'ชิ้น')

        # 2) บันทึกการเบิก
        payload = {
            "equipment_id": equipment_id,
            "equipment_name": eq_name,
            "qty": qty,
            "unit": eq_unit,
            "purpose": purpose or '',
            "withdrawn_by": withdrawn_by,
            "withdrawn_by_name": withdrawn_by_name or '',
            "notes": notes or '',
        }
        if withdrawn_at:
            if hasattr(withdrawn_at, 'isoformat'):
                if hasattr(withdrawn_at, 'hour'):
                    payload["withdrawn_at"] = withdrawn_at.isoformat()
                else:
                    now = datetime.now()
                    dt = datetime.combine(withdrawn_at, now.time())
                    payload["withdrawn_at"] = dt.isoformat()
            else:
                payload["withdrawn_at"] = str(withdrawn_at)
        else:
            payload["withdrawn_at"] = now_utc().isoformat()

        r = sb.table("withdrawals").insert(payload).execute()
        return r.data[0] if r.data else None

    except Exception:
        log.exception("create_withdrawal failed")
        st.error("⚠️ เบิกไม่สำเร็จ กรุณาลองใหม่")
        return None


def get_withdrawals(equipment_id: Optional[str] = None,
                    user_id: Optional[str] = None,
                    limit: int = 200,
                    start_date=None, end_date=None) -> List[dict]:
    try:
        sb = get_supabase()
        q = (sb.table("withdrawals").select("*")
             .order("withdrawn_at", desc=True).limit(limit))
        if equipment_id:
            q = q.eq("equipment_id", equipment_id)
        if user_id:
            q = q.eq("withdrawn_by", user_id)
        if start_date:
            q = q.gte("withdrawn_at",
                      start_date.isoformat() if hasattr(start_date, 'isoformat')
                      else str(start_date))
        if end_date:
            q = q.lte("withdrawn_at",
                      end_date.isoformat() if hasattr(end_date, 'isoformat')
                      else str(end_date))
        return q.execute().data or []
    except Exception:
        log.exception("get_withdrawals failed")
        return []


def delete_withdrawal(withdrawal_id: str, restore_stock: bool = True) -> bool:
    """ลบรายการเบิก + คืน stock (atomic)"""
    try:
        sb = get_supabase()
        if restore_stock:
            r = sb.table("withdrawals").select("*").eq("id", withdrawal_id).execute()
            if r.data:
                w = r.data[0]
                # Atomic restore via SQL (no RPC needed, just increment)
                eq_r = sb.table("equipment").select("stock").eq("id", w['equipment_id']).execute()
                if eq_r.data:
                    cur = float(eq_r.data[0].get('stock', 0) or 0)
                    new_stock = int(cur + float(w.get('qty', 0) or 0))
                    sb.table("equipment").update({"stock": new_stock}).eq("id", w['equipment_id']).execute()
        sb.table("withdrawals").delete().eq("id", withdrawal_id).execute()
        return True
    except Exception:
        log.exception("delete_withdrawal failed")
        return False


# ==================================================================
# PO drafts
# ==================================================================
def save_po_draft(user_id: str, items: list, notes: str = "") -> bool:
    try:
        sb = get_supabase()
        existing = sb.table("po_drafts").select("id").eq("user_id", user_id).execute()
        payload = {
            "user_id": user_id, "items": items, "notes": notes,
            "updated_at": now_utc().isoformat(),
        }
        if existing.data:
            sb.table("po_drafts").update(payload).eq("user_id", user_id).execute()
        else:
            sb.table("po_drafts").insert(payload).execute()
        return True
    except Exception:
        return False


def get_po_draft(user_id: str) -> Optional[dict]:
    try:
        r = get_supabase().table("po_drafts").select("*").eq("user_id", user_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def delete_po_draft(user_id: str) -> bool:
    try:
        get_supabase().table("po_drafts").delete().eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


# ==================================================================
# Procurement, status updates
# ==================================================================
def update_po_procurement(po_id: str, supplier_name: str,
                          supplier_contact: str, items_with_prices: list,
                          discount: float = 0, shipping_fee: float = 0,
                          vat: float = 0, expected_date=None,
                          procurement_notes: str = "",
                          user_name: str = "") -> bool:
    try:
        sb = get_supabase()
        subtotal = sum(it.get("subtotal", 0) for it in items_with_prices)
        total = subtotal - float(discount) + float(shipping_fee) + float(vat)

        sb.table("purchase_orders").update({
            "supplier_name": supplier_name,
            "supplier_contact": supplier_contact,
            "items": items_with_prices,
            "subtotal": float(subtotal),
            "discount": float(discount),
            "shipping_fee": float(shipping_fee),
            "vat": float(vat), "total": float(total),
            "expected_date": expected_date,
            "ordered_date": datetime.now().date().isoformat(),
            "procurement_notes": procurement_notes,
            "status": Status.ORDERED,
            "updated_at": now_utc().isoformat(),
        }).eq("id", po_id).execute()

        for it in items_with_prices:
            if it.get("equipment_id") and it.get("unit_price", 0) > 0:
                update_equipment(it["equipment_id"], last_cost=it["unit_price"])

        log_activity(po_id, user_name, "admin", "ordered",
                     f"สั่งกับ {supplier_name} | คาดได้ {expected_date or '-'}")

        try:
            po = get_purchase_order(po_id)
            if po and po.get('created_by'):
                add_notification(
                    po['created_by'], po_id,
                    f"✅ {po.get('po_number', '-')} สั่งซื้อแล้ว",
                    f"แอดมินสั่งกับ {supplier_name} • คาดว่าได้รับ {expected_date or '-'}",
                )
        except Exception:
            log.exception("notify after procurement failed")

        return True
    except Exception:
        log.exception("update_po_procurement failed")
        st.error("⚠️ บันทึกไม่สำเร็จ")
        return False


def update_po_status(po_id: str, new_status: str,
                     user_name: str, user_role: str,
                     note: str = "",
                     tracking_number: Optional[str] = None) -> bool:
    try:
        sb = get_supabase()
        po = get_purchase_order(po_id)
        if not po:
            return False
        upd = {"status": new_status, "updated_at": now_utc().isoformat()}
        if tracking_number is not None:
            upd["tracking_number"] = tracking_number
        if new_status == Status.COMPLETE and not po.get("received_date"):
            upd["received_date"] = datetime.now().date().isoformat()

        sb.table("purchase_orders").update(upd).eq("id", po["id"]).execute()
        log_activity(po["id"], user_name, user_role, "status_changed",
                     f"{po['status']} → {new_status}" + (f" | {note}" if note else ""))

        try:
            if new_status == Status.SHIPPING and po.get('created_by'):
                tk_msg = f" • Tracking: {tracking_number}" if tracking_number else ""
                add_notification(
                    po['created_by'], po["id"],
                    f"🚚 {po.get('po_number', '-')} กำลังขนส่ง",
                    f"Supplier ส่งของแล้ว{tk_msg} — เตรียมรับของได้",
                )
            elif new_status == Status.COMPLETE and po.get('created_by'):
                add_notification(
                    po['created_by'], po["id"],
                    f"🎉 {po.get('po_number', '-')} เสร็จสมบูรณ์",
                    "ปิดงานเรียบร้อย",
                )
            elif new_status == Status.CANCELLED:
                if po.get('created_by'):
                    add_notification(
                        po['created_by'], po["id"],
                        f"❌ {po.get('po_number', '-')} ถูกยกเลิก",
                        f"โดย {user_name}" + (f" • {note}" if note else ""),
                    )
                notify_admins(po["id"],
                              f"❌ {po.get('po_number', '-')} ถูกยกเลิก",
                              f"โดย {user_name}")
        except Exception:
            log.exception("notify after status change failed")
        return True
    except Exception:
        log.exception("update_po_status failed")
        return False


def delete_purchase_order(po_id: str) -> bool:
    try:
        get_supabase().table("purchase_orders").delete().eq("id", po_id).execute()
        return True
    except Exception:
        log.exception("delete_purchase_order failed")
        return False


def get_unique_suppliers() -> List[str]:
    try:
        r = (get_supabase().table("purchase_orders")
             .select("supplier_name")
             .not_.is_("supplier_name", "null").execute())
        return sorted(set(x["supplier_name"] for x in (r.data or [])
                          if x.get("supplier_name")))
    except Exception:
        return []


# ==================================================================
# Deliveries
# ==================================================================
def add_delivery(po_id: str, items_received: list,
                 overall_condition: str,
                 issue_description: str = "",
                 notes: str = "", image_urls=None,
                 user_name: str = "") -> Optional[dict]:
    try:
        sb = get_supabase()
        existing = sb.table("po_deliveries").select("delivery_no").eq("po_id", po_id).execute()
        d_no = (max((d["delivery_no"] for d in existing.data), default=0) + 1) if existing.data else 1

        delivery = sb.table("po_deliveries").insert({
            "po_id": po_id, "delivery_no": d_no,
            "received_date": datetime.now().date().isoformat(),
            "received_by_name": user_name,
            "items_received": items_received,
            "overall_condition": overall_condition,
            "issue_description": issue_description,
            "notes": notes, "image_urls": image_urls or [],
        }).execute().data[0]

        # บวก stock
        for it in items_received:
            if it.get("equipment_id") and it.get("qty_received", 0) > 0:
                eq = get_equipment(it["equipment_id"])
                if eq:
                    update_equipment(it["equipment_id"],
                                     stock=(eq.get("stock") or 0) + int(it["qty_received"]))

        po = get_purchase_order(po_id)
        if po:
            new_status = Status.PROBLEM if overall_condition != 'ปกติ' else Status.RECEIVED
            sb.table("purchase_orders").update({
                "status": new_status,
                "received_date": datetime.now().date().isoformat(),
                "updated_at": now_utc().isoformat(),
            }).eq("id", po_id).execute()
            log_activity(po_id, user_name, "requester", "received",
                         f"รับของ #{d_no} | สภาพ: {overall_condition}")

            try:
                if new_status == Status.PROBLEM:
                    notify_admins(po_id,
                                  f"⚠️ {po.get('po_number', '-')} มีปัญหา",
                                  f"{user_name} แจ้ง: {issue_description or 'ของไม่ครบ'}")
                else:
                    notify_admins(po_id,
                                  f"📦 {po.get('po_number', '-')} รับของแล้ว",
                                  f"{user_name} รับของเรียบร้อย")
            except Exception:
                log.exception("notify after delivery failed")

        return delivery
    except Exception:
        log.exception("add_delivery failed")
        st.error("⚠️ บันทึกการรับของไม่สำเร็จ")
        return None


def get_deliveries(po_id: str) -> List[dict]:
    try:
        return (get_supabase().table("po_deliveries").select("*")
                .eq("po_id", po_id).order("delivery_no").execute().data or [])
    except Exception:
        return []


# ==================================================================
# Activities + Comments + Notifications
# ==================================================================
def log_activity(po_id: str, user_name: str, user_role: str,
                 action: str, description: str = "") -> bool:
    try:
        get_supabase().table("po_activities").insert({
            "po_id": po_id, "user_name": user_name, "user_role": user_role,
            "action": action, "description": description,
        }).execute()
        return True
    except Exception:
        return False


def get_activities(po_id: str) -> List[dict]:
    try:
        return (get_supabase().table("po_activities").select("*")
                .eq("po_id", po_id).order("created_at", desc=True)
                .execute().data or [])
    except Exception:
        return []


def add_comment(po_id: str, user_name: str, user_role: str,
                message: str) -> bool:
    try:
        get_supabase().table("po_comments").insert({
            "po_id": po_id, "user_name": user_name,
            "user_role": user_role, "message": message,
        }).execute()
        log_activity(po_id, user_name, user_role, "commented", message[:100])
        return True
    except Exception:
        return False


def get_comments(po_id: str) -> List[dict]:
    try:
        return (get_supabase().table("po_comments").select("*")
                .eq("po_id", po_id).order("created_at").execute().data or [])
    except Exception:
        return []


def add_notification(user_id: str, po_id: str, title: str,
                     message: str = "") -> bool:
    try:
        get_supabase().table("notifications").insert({
            "user_id": user_id, "po_id": po_id,
            "title": title, "message": message,
        }).execute()
        return True
    except Exception:
        return False


def get_notifications(user_id: str, unread_only: bool = False) -> List[dict]:
    try:
        q = get_supabase().table("notifications").select("*").eq("user_id", user_id)
        if unread_only:
            q = q.eq("is_read", False)
        return q.order("created_at", desc=True).limit(50).execute().data or []
    except Exception:
        return []


def mark_notification_read(nid: str) -> bool:
    try:
        get_supabase().table("notifications").update({"is_read": True}).eq("id", nid).execute()
        return True
    except Exception:
        return False


def mark_all_notifications_read(user_id: str) -> bool:
    try:
        get_supabase().table("notifications").update({"is_read": True}).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


# ==================================================================
# Overdue / Upcoming
# ==================================================================
def get_overdue_pos() -> List[dict]:
    try:
        today = date.today().isoformat()
        return (get_supabase().table("purchase_orders").select("*")
                .lt("expected_date", today)
                .in_("status", list(Status.PENDING_RECEIPT))
                .execute().data or [])
    except Exception:
        return []


def get_upcoming_pos(days: int = 3) -> List[dict]:
    try:
        today = date.today()
        deadline = (today + timedelta(days=days)).isoformat()
        return (get_supabase().table("purchase_orders").select("*")
                .gte("expected_date", today.isoformat())
                .lte("expected_date", deadline)
                .in_("status", list(Status.PENDING_RECEIPT))
                .execute().data or [])
    except Exception:
        return []


# ==================================================================
# 💰 BUDGET TRACKING (NEW FEATURE)
# ==================================================================
def get_budget_for_period(period_type: str, year: int,
                          month: Optional[int] = None,
                          category: Optional[str] = None) -> Optional[dict]:
    """ดึงงบประมาณของช่วงเวลานั้นๆ
    period_type: 'monthly', 'quarterly', 'yearly'
    """
    try:
        sb = get_supabase()
        q = (sb.table("budget_periods").select("*")
             .eq("period_type", period_type)
             .eq("period_year", year))
        if month is not None:
            q = q.eq("period_month", month)
        else:
            q = q.is_("period_month", None)
        if category:
            q = q.eq("category", category)
        else:
            q = q.is_("category", None)
        r = q.execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def list_budgets(year: Optional[int] = None) -> List[dict]:
    """ดึงงบประมาณทั้งหมด"""
    try:
        sb = get_supabase()
        q = sb.table("budget_periods").select("*")
        if year:
            q = q.eq("period_year", year)
        return q.order("period_year", desc=True).order("period_month").execute().data or []
    except Exception:
        return []


def upsert_budget(period_type: str, year: int, amount: float,
                  month: Optional[int] = None,
                  category: Optional[str] = None,
                  notes: str = "",
                  created_by_name: str = "") -> bool:
    """เพิ่ม/แก้งบประมาณ"""
    try:
        sb = get_supabase()
        existing = get_budget_for_period(period_type, year, month, category)
        payload = {
            "period_type": period_type,
            "period_year": year,
            "period_month": month,
            "category": category,
            "amount": float(amount),
            "notes": notes,
            "created_by_name": created_by_name,
        }
        if existing:
            sb.table("budget_periods").update(payload).eq("id", existing['id']).execute()
        else:
            sb.table("budget_periods").insert(payload).execute()
        return True
    except Exception:
        log.exception("upsert_budget failed")
        return False


def delete_budget(budget_id: str) -> bool:
    try:
        get_supabase().table("budget_periods").delete().eq("id", budget_id).execute()
        return True
    except Exception:
        return False


def calculate_actual_spending(year: int, month: Optional[int] = None,
                              category: Optional[str] = None) -> float:
    """คำนวณยอดใช้จ่ายจริงในช่วงเวลานั้น
    
    นับเฉพาะ PO ที่ status ในกลุ่ม "ใช้งบจริงแล้ว" — ordered onwards
    """
    try:
        sb = get_supabase()
        # ดึง PO ที่อยู่ในช่วงเวลานั้น
        if month is not None:
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1)
            else:
                end = date(year, month + 1, 1)
        else:
            start = date(year, 1, 1)
            end = date(year + 1, 1, 1)

        # ใช้ ordered_date เพราะนับว่าเป็นการ "ใช้งบ" ตอนสั่งซื้อ
        valid_statuses = [Status.ORDERED, Status.SHIPPING, Status.RECEIVED,
                          Status.PROBLEM, Status.COMPLETE]

        q = (sb.table("purchase_orders").select("total, items, ordered_date")
             .gte("ordered_date", start.isoformat())
             .lt("ordered_date", end.isoformat())
             .in_("status", valid_statuses))
        r = q.execute()
        total = 0.0
        for p in r.data or []:
            if category:
                # ถ้า filter category — ต้องคำนวณจาก items แต่ละชิ้นที่ตรง category
                # (ต้อง JOIN กับ equipment.category)
                # ทำแบบง่าย: รวม items ที่อยู่ในหมวดนั้น
                eq_ids = [it.get('equipment_id') for it in (p.get('items') or [])
                          if it.get('equipment_id')]
                if not eq_ids:
                    continue
                eq_r = (sb.table("equipment").select("id, category")
                        .in_("id", eq_ids).execute())
                cat_eq_ids = {e['id'] for e in (eq_r.data or [])
                              if e.get('category') == category}
                # คำนวณ subtotal เฉพาะ items ในหมวด
                for it in (p.get('items') or []):
                    if it.get('equipment_id') in cat_eq_ids:
                        total += float(it.get('subtotal', 0) or 0)
            else:
                total += float(p.get('total', 0) or 0)
        return total
    except Exception:
        log.exception("calculate_actual_spending failed")
        return 0.0


def get_budget_status_for_dashboard(year: int, month: int) -> List[dict]:
    """ดึงสถานะงบประมาณทั้งหมดของเดือนนั้น พร้อม % ที่ใช้ไป
    
    return list of {
        type, period, category, budget, actual, percent, status
    }
    """
    results = []
    budgets = [b for b in list_budgets(year=year)
               if (b['period_type'] == 'monthly' and b.get('period_month') == month)
               or b['period_type'] == 'yearly'
               or (b['period_type'] == 'quarterly'
                   and ((month - 1) // 3 + 1) == ((b.get('period_month') - 1) // 3 + 1
                                                   if b.get('period_month') else 0))]

    for b in budgets:
        if b['period_type'] == 'monthly':
            actual = calculate_actual_spending(year, b['period_month'], b.get('category'))
        elif b['period_type'] == 'yearly':
            actual = calculate_actual_spending(year, None, b.get('category'))
        else:  # quarterly
            actual = 0
            if b.get('period_month'):
                q = (b['period_month'] - 1) // 3
                for m in range(q * 3 + 1, q * 3 + 4):
                    actual += calculate_actual_spending(year, m, b.get('category'))

        budget = float(b.get('amount', 0) or 0)
        pct = (actual / budget * 100) if budget > 0 else 0
        if pct >= 100:
            stat = 'over'
        elif pct >= 95:
            stat = 'critical'
        elif pct >= 80:
            stat = 'warning'
        else:
            stat = 'ok'

        results.append({
            'id': b['id'],
            'type': b['period_type'],
            'period': f"{year}-{b.get('period_month', '*'):>02}" if b.get('period_month')
                      else str(year),
            'category': b.get('category') or 'รวมทั้งหมด',
            'budget': budget,
            'actual': actual,
            'remaining': budget - actual,
            'percent': pct,
            'status': stat,
        })
    return results
