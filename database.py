"""database.py — Supabase wrapper สำหรับ PO Pro"""
import os, uuid, hashlib
from datetime import datetime, date, timedelta
from typing import Optional
import streamlit as st
from supabase import create_client, Client


ROLES = {'requester': 'ผู้สั่ง', 'admin': 'แอดมิน + จัดซื้อ'}

PO_STATUSES = [
    "รอจัดซื้อดำเนินการ", "สั่งซื้อแล้ว", "กำลังขนส่ง",
    "รับของแล้ว", "มีปัญหา", "เสร็จสมบูรณ์", "ยกเลิก",
]

STATUS_EMOJI = {
    "รอจัดซื้อดำเนินการ": "📝",
    "สั่งซื้อแล้ว": "✅",
    "กำลังขนส่ง": "🚚",
    "รับของแล้ว": "📦",
    "มีปัญหา": "⚠️",
    "เสร็จสมบูรณ์": "✓",
    "ยกเลิก": "❌",
}

DEFAULT_CATEGORIES = ["ขวดบรรจุ", "ฝา/จุก", "กล่องบรรจุภัณฑ์", "สติกเกอร์/ฉลาก", "อุปกรณ์อื่นๆ"]
IMG_EQ = "equipment-images"
IMG_DEL = "delivery-images"
IMG_ATTACH = "po-attachments"


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


# --- Auth & Security ---
import re
import secrets as _py_secrets


def hash_password(p):
    """SHA-256 hash with salt (production should use bcrypt)"""
    return hashlib.sha256(p.encode()).hexdigest()


def validate_password(pwd, username=""):
    """ตรวจรหัสผ่าน — คืน (ok: bool, message: str)"""
    if not pwd or len(pwd) < 8:
        return False, "รหัสผ่านต้องยาวอย่างน้อย 8 ตัวอักษร"
    if pwd.lower() == username.lower():
        return False, "รหัสผ่านห้ามเหมือน username"
    if not re.search(r'[A-Za-z]', pwd):
        return False, "ต้องมีตัวอักษรอย่างน้อย 1 ตัว"
    if not re.search(r'[0-9]', pwd):
        return False, "ต้องมีตัวเลขอย่างน้อย 1 ตัว"
    weak = ['password', '12345678', 'qwerty', 'admin123', 'staff123']
    if pwd.lower() in weak:
        return False, "รหัสผ่านนี้อ่อนแอเกินไป — เปลี่ยนเป็นรหัสที่คาดเดายากกว่านี้"
    return True, "OK"


def verify_user(username, password, ip_hash=None):
    """ตรวจ login + log ความพยายาม"""
    sb = get_supabase()
    try:
        # ตรวจล็อคถูกล็อคไหม (ผิด > 5 ครั้งใน 15 นาที)
        if _is_account_locked(username):
            return None  # ส่ง None แต่ caller ควรเช็ค locked status แยก

        h = hash_password(password)
        res = sb.table("users").select("*").eq("username", username).eq("password_hash", h).eq("is_active", True).execute()

        if res.data:
            user = res.data[0]
            _log_login(username, success=True)
            # update last_login
            try:
                sb.table("users").update({
                    "last_login_at": datetime.now().isoformat(),
                    "failed_login_count": 0,
                }).eq("id", user["id"]).execute()
            except Exception:
                pass
            return user
        else:
            _log_login(username, success=False)
            return None
    except Exception:
        return None


def _is_account_locked(username):
    """เช็คว่า account ล็อคหรือไม่ (ผิดเกิน 5 ครั้งใน 15 นาที)"""
    sb = get_supabase()
    try:
        cutoff = (datetime.now() - timedelta(minutes=15)).isoformat()
        res = sb.table("login_attempts").select("*").eq("username", username).eq("success", False).gte("created_at", cutoff).execute()
        return len(res.data or []) >= 5
    except Exception:
        return False


def get_failed_attempts_count(username):
    """จำนวนครั้งที่ผิดใน 15 นาที"""
    sb = get_supabase()
    try:
        cutoff = (datetime.now() - timedelta(minutes=15)).isoformat()
        res = sb.table("login_attempts").select("id").eq("username", username).eq("success", False).gte("created_at", cutoff).execute()
        return len(res.data or [])
    except Exception:
        return 0


def _log_login(username, success):
    """บันทึก login attempt"""
    sb = get_supabase()
    try:
        sb.table("login_attempts").insert({
            "username": username,
            "success": success,
        }).execute()
    except Exception:
        pass


def get_users():
    try:
        return get_supabase().table("users").select("*").order("created_at").execute().data or []
    except Exception:
        return []


def get_user(uid):
    try:
        r = get_supabase().table("users").select("*").eq("id", uid).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def add_user(username, password, full_name, role="requester", email=""):
    """เพิ่มผู้ใช้ — auto enforce password policy"""
    ok, msg = validate_password(password, username)
    if not ok:
        st.error(f"❌ {msg}")
        return None
    try:
        return get_supabase().table("users").insert({
            "username": username, "password_hash": hash_password(password),
            "full_name": full_name, "role": role, "email": email,
            "must_change_password": True,  # บังคับเปลี่ยนรหัสครั้งแรก
        }).execute().data[0]
    except Exception as e:
        st.error(f"เพิ่มผู้ใช้ไม่สำเร็จ: {e}")
        return None


def update_user(uid, **fields):
    try:
        if "password" in fields:
            new_pwd = fields.pop("password")
            user = get_user(uid)
            uname_check = user.get('username', '') if user else ''
            ok, msg = validate_password(new_pwd, uname_check)
            if not ok:
                st.error(f"❌ {msg}")
                return False
            fields["password_hash"] = hash_password(new_pwd)
            fields["must_change_password"] = False
            fields["password_changed_at"] = datetime.now().isoformat()
        get_supabase().table("users").update(fields).eq("id", uid).execute()
        return True
    except Exception:
        return False


def delete_user(uid):
    try:
        get_supabase().table("users").delete().eq("id", uid).execute()
        return True
    except Exception:
        return False


# --- Categories ---
def get_categories():
    """ดึงหมวดทั้งหมด เรียงตาม display_order"""
    try:
        sb = get_supabase()
        # ลองเรียงตาม display_order ก่อน, fallback created_at
        try:
            r = sb.table("equipment_categories").select("name").order("display_order").order("created_at").execute()
        except Exception:
            r = sb.table("equipment_categories").select("name").order("created_at").execute()
        cats = [x["name"] for x in r.data]
        if not cats:
            for n in DEFAULT_CATEGORIES:
                sb.table("equipment_categories").insert({"name": n}).execute()
            return DEFAULT_CATEGORIES.copy()
        return cats
    except Exception:
        return DEFAULT_CATEGORIES.copy()


def get_categories_with_order():
    """ดึงหมวด + ลำดับ (สำหรับหน้าจัดการ)"""
    try:
        sb = get_supabase()
        try:
            r = sb.table("equipment_categories").select("*").order("display_order").order("created_at").execute()
        except Exception:
            r = sb.table("equipment_categories").select("*").order("created_at").execute()
        return r.data or []
    except Exception:
        return []


def add_category(name):
    try:
        sb = get_supabase()
        # หาลำดับสูงสุดแล้วต่อท้าย
        try:
            mx = sb.table("equipment_categories").select("display_order").order("display_order", desc=True).limit(1).execute()
            next_order = (mx.data[0].get("display_order") or 0) + 1 if mx.data else 1
        except Exception:
            next_order = 999
        try:
            sb.table("equipment_categories").insert({
                "name": name, "display_order": next_order,
            }).execute()
        except Exception:
            # fallback ถ้ายังไม่มี column
            sb.table("equipment_categories").insert({"name": name}).execute()
        return True
    except Exception:
        return False


def move_category(name, direction):
    """เลื่อนหมวดขึ้น/ลง — direction = 'up' หรือ 'down'"""
    try:
        sb = get_supabase()
        # ดึงทั้งหมดเรียงตามลำดับ
        cats = get_categories_with_order()
        if not cats:
            return False
        idx = next((i for i, c in enumerate(cats) if c['name'] == name), -1)
        if idx < 0:
            return False
        if direction == 'up' and idx == 0:
            return False  # บนสุดอยู่แล้ว
        if direction == 'down' and idx == len(cats) - 1:
            return False  # ล่างสุดอยู่แล้ว

        target_idx = idx - 1 if direction == 'up' else idx + 1
        a = cats[idx]
        b = cats[target_idx]

        # สลับ display_order
        ord_a = a.get('display_order', idx + 1)
        ord_b = b.get('display_order', target_idx + 1)
        sb.table("equipment_categories").update({"display_order": ord_b}).eq("id", a['id']).execute()
        sb.table("equipment_categories").update({"display_order": ord_a}).eq("id", b['id']).execute()
        return True
    except Exception as e:
        st.error(f"ย้ายไม่สำเร็จ: {e}")
        return False


def update_category(old_name, new_name):
    """เปลี่ยนชื่อหมวด + อัปเดต equipment ที่อ้างถึง"""
    try:
        sb = get_supabase()
        # 1) update ชื่อหมวด
        sb.table("equipment_categories").update({"name": new_name}).eq("name", old_name).execute()
        # 2) อัปเดต equipment ที่ใช้หมวดเดิม
        sb.table("equipment").update({"category": new_name}).eq("category", old_name).execute()
        return True
    except Exception as e:
        st.error(f"แก้ไขไม่สำเร็จ: {e}")
        return False


def delete_category(name):
    """ลบหมวด — ต้องไม่มีสินค้าอยู่ในหมวดนี้"""
    try:
        sb = get_supabase()
        # ตรวจว่ามีสินค้าใน category นี้หรือเปล่า
        c = sb.table("equipment").select("id", count="exact").eq("category", name).eq("is_active", True).execute()
        if c.count and c.count > 0:
            return False, f"มีสินค้า {c.count} รายการในหมวดนี้ — ย้ายหรือลบสินค้าก่อน"
        sb.table("equipment_categories").delete().eq("name", name).execute()
        return True, "ลบเรียบร้อย"
    except Exception as e:
        return False, str(e)


def count_equipment_by_category(name):
    """นับจำนวนสินค้า active ในหมวด"""
    try:
        sb = get_supabase()
        r = sb.table("equipment").select("id", count="exact").eq("category", name).eq("is_active", True).execute()
        return r.count or 0
    except Exception:
        return 0


# --- Image upload ---
def upload_image(file_bytes, filename, bucket=IMG_EQ):
    sb = get_supabase()
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    new_fn = f"{uuid.uuid4().hex}.{ext}"
    ct = f"image/{'jpeg' if ext == 'jpg' else ext}"
    try:
        sb.storage.from_(bucket).upload(path=new_fn, file=file_bytes,
                                          file_options={"content-type": ct, "upsert": "false"})
        return sb.storage.from_(bucket).get_public_url(new_fn)
    except Exception as e:
        st.error(f"อัปโหลดไม่สำเร็จ: {e}")
        return None


# Mapping ext → mime type สำหรับ attachment
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
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'zip': 'application/zip',
    'rar': 'application/x-rar-compressed',
    '7z': 'application/x-7z-compressed',
}


def upload_attachment(file_bytes, filename, bucket=IMG_ATTACH):
    """อัปโหลดไฟล์แนบ (PDF, Word, Excel, รูป, etc.)
    คืน dict {'url', 'name', 'size', 'type'} หรือ None"""
    sb = get_supabase()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    content_type = ATTACHMENT_MIMES.get(ext, "application/octet-stream")
    # เก็บชื่อจริงไว้ + ใช้ UUID นำหน้าเพื่อกัน collision
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
            'uploaded_at': datetime.now().isoformat(),
        }
    except Exception as e:
        st.error(f"อัปโหลดไม่สำเร็จ ({filename}): {e}")
        return None


def add_po_attachments(po_id, new_attachments, user_name="", category="general"):
    """เพิ่มไฟล์แนบเข้า PO (รวมกับของเดิม)
    new_attachments: list ของ dict {url, name, size, type, ...}"""
    if not new_attachments:
        return False
    sb = get_supabase()
    try:
        po = get_purchase_order(po_id)
        if not po:
            return False
        existing = po.get('attachment_urls') or []
        # tag category + uploader
        for a in new_attachments:
            a['category'] = category
            a['uploaded_by'] = user_name
        merged = existing + new_attachments
        sb.table("purchase_orders").update({
            "attachment_urls": merged,
            "updated_at": datetime.now().isoformat(),
        }).eq("id", po_id).execute()
        return True
    except Exception as e:
        st.error(f"บันทึกไฟล์แนบไม่สำเร็จ: {e}")
        return False


def remove_po_attachment(po_id, attachment_url):
    """ลบไฟล์แนบ 1 รายการ ออกจาก PO (ลบเฉพาะ reference ในตาราง — ไฟล์ยังอยู่ใน storage)"""
    sb = get_supabase()
    try:
        po = get_purchase_order(po_id)
        if not po:
            return False
        existing = po.get('attachment_urls') or []
        new_list = [a for a in existing if a.get('url') != attachment_url]
        sb.table("purchase_orders").update({
            "attachment_urls": new_list,
            "updated_at": datetime.now().isoformat(),
        }).eq("id", po_id).execute()
        return True
    except Exception:
        return False


# --- Equipment ---
def get_equipment_list(active_only=False):
    try:
        sb = get_supabase()
        q = sb.table("equipment").select("*")
        if active_only:
            q = q.eq("is_active", True)
        return q.order("created_at", desc=True).execute().data or []
    except Exception:
        return []


def get_equipment(eid):
    try:
        r = get_supabase().table("equipment").select("*").eq("id", eid).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def add_equipment(name, category, unit="ชิ้น", sku="", description="",
                  last_cost=0, stock=0, image_url=None, image_urls=None):
    try:
        # รวม image_url เก่ากับ image_urls ใหม่
        urls_list = list(image_urls or [])
        if image_url and image_url not in urls_list:
            urls_list.insert(0, image_url)
        # primary image = รูปแรก
        primary = urls_list[0] if urls_list else None
        return get_supabase().table("equipment").insert({
            "name": name, "category": category, "unit": unit, "sku": sku,
            "description": description, "last_cost": float(last_cost),
            "stock": int(stock),
            "image_url": primary,
            "image_urls": urls_list,
            "is_active": True,
        }).execute().data[0]
    except Exception as e:
        st.error(f"เพิ่มไม่สำเร็จ: {e}")
        return None


def update_equipment(eid, **fields):
    try:
        if "last_cost" in fields:
            fields["last_cost"] = float(fields["last_cost"])
        if "stock" in fields:
            fields["stock"] = int(fields["stock"])
        # ถ้ามี image_urls ให้ sync image_url (รูปแรก) ด้วย
        if "image_urls" in fields:
            urls = fields["image_urls"] or []
            fields["image_url"] = urls[0] if urls else None
        get_supabase().table("equipment").update(fields).eq("id", eid).execute()
        return True
    except Exception:
        return False


def add_equipment_image(eid, image_url):
    """เพิ่มรูปใน array (ไม่ลบของเดิม)"""
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


def remove_equipment_image(eid, image_url):
    """ลบรูป 1 รูปออกจาก array"""
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


def delete_equipment(eid):
    try:
        get_supabase().table("equipment").delete().eq("id", eid).execute()
        return True
    except Exception:
        return False


# --- Purchase Orders ---
def generate_po_number():
    sb = get_supabase()
    year = datetime.now().year
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
        return f"PO-{year}-{datetime.now().strftime('%H%M%S')}"


def get_purchase_orders(user_id=None, role="requester", status_filter=None):
    try:
        sb = get_supabase()
        q = sb.table("purchase_orders").select("*")
        if role == "requester" and user_id:
            q = q.eq("created_by", user_id)
        if status_filter and status_filter != "ทั้งหมด":
            q = q.eq("status", status_filter)
        return q.order("created_at", desc=True).execute().data or []
    except Exception as e:
        st.error(f"ดึง PO ไม่สำเร็จ: {e}")
        return []


def get_pos_pending_receipt():
    """ดึง PO ที่รอรับของ (สถานะ สั่งซื้อแล้ว / กำลังขนส่ง) — staff ทุกคนเห็นได้"""
    try:
        sb = get_supabase()
        q = sb.table("purchase_orders").select("*").in_(
            "status", ["สั่งซื้อแล้ว", "กำลังขนส่ง"]
        )
        return q.order("expected_date", desc=False).execute().data or []
    except Exception as e:
        st.error(f"ดึง PO รอรับของไม่สำเร็จ: {e}")
        return []


def get_purchase_order(po_id):
    try:
        sb = get_supabase()
        if "-" in po_id and len(po_id) == 36:
            r = sb.table("purchase_orders").select("*").eq("id", po_id).execute()
        else:
            r = sb.table("purchase_orders").select("*").eq("po_number", po_id).execute()
        return r.data[0] if r.data else None
    except Exception:
        return None


def create_purchase_order(items, purpose="", notes="", created_by=None, created_by_name=""):
    """ผู้สั่งสร้าง PO - ยังไม่มีราคา/supplier"""
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
        } for it in items]

        po = sb.table("purchase_orders").insert({
            "po_number": po_no, "items": clean,
            "purpose": purpose, "notes": notes,
            "status": "รอจัดซื้อดำเนินการ",
            "created_by": created_by, "created_by_name": created_by_name,
        }).execute().data[0]
        log_activity(po["id"], created_by_name, "requester", "created",
                      f"สร้าง PO มี {len(items)} รายการ")
        return po
    except Exception as e:
        st.error(f"สร้างไม่สำเร็จ: {e}")
        return None


def clone_purchase_order(source_po_id, created_by, created_by_name):
    """คัดลอก PO เก่าเป็นใบใหม่ — เก็บ items + purpose + notes แต่ reset status/dates/supplier"""
    try:
        source = get_purchase_order(source_po_id)
        if not source:
            return None
        # Clone items แบบ reset ราคา (ผู้สั่งไม่ควรเห็นราคาเดิม)
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
            items=items,
            purpose=f"[คัดลอกจาก {source['po_number']}] {source.get('purpose', '')}",
            notes=source.get('notes', ''),
            created_by=created_by,
            created_by_name=created_by_name,
        )
        if new_po:
            log_activity(new_po['id'], created_by_name, "requester", "cloned",
                          f"คัดลอกจาก {source['po_number']}")
        return new_po
    except Exception as e:
        st.error(f"คัดลอกไม่สำเร็จ: {e}")
        return None


def get_low_stock_equipment(threshold=10):
    """ดึงอุปกรณ์ที่สต็อกต่ำกว่า threshold (เริ่มต้น 10)"""
    try:
        return get_supabase().table("equipment").select("*").lt("stock", threshold).eq("is_active", True).execute().data or []
    except Exception:
        return []


def update_po_procurement(po_id, supplier_name, supplier_contact, items_with_prices,
                           discount=0, shipping_fee=0, vat=0, expected_date=None,
                           procurement_notes="", user_name=""):
    """จัดซื้อกรอกข้อมูล supplier + ราคา"""
    try:
        sb = get_supabase()
        subtotal = sum(it.get("subtotal", 0) for it in items_with_prices)
        total = subtotal - float(discount) + float(shipping_fee) + float(vat)

        sb.table("purchase_orders").update({
            "supplier_name": supplier_name, "supplier_contact": supplier_contact,
            "items": items_with_prices, "subtotal": float(subtotal),
            "discount": float(discount), "shipping_fee": float(shipping_fee),
            "vat": float(vat), "total": float(total),
            "expected_date": expected_date,
            "ordered_date": datetime.now().date().isoformat(),
            "procurement_notes": procurement_notes,
            "status": "สั่งซื้อแล้ว",
            "updated_at": datetime.now().isoformat(),
        }).eq("id", po_id).execute()

        for it in items_with_prices:
            if it.get("equipment_id") and it.get("unit_price", 0) > 0:
                update_equipment(it["equipment_id"], last_cost=it["unit_price"])

        log_activity(po_id, user_name, "admin", "ordered",
                      f"สั่งกับ {supplier_name} | คาดได้ {expected_date or '-'}")
        return True
    except Exception as e:
        st.error(f"ไม่สำเร็จ: {e}")
        return False


def update_po_status(po_id, new_status, user_name, user_role, note="", tracking_number=None):
    try:
        sb = get_supabase()
        po = get_purchase_order(po_id)
        if not po:
            return False
        upd = {"status": new_status, "updated_at": datetime.now().isoformat()}
        if tracking_number is not None:
            upd["tracking_number"] = tracking_number
        if new_status == "เสร็จสมบูรณ์" and not po.get("received_date"):
            upd["received_date"] = datetime.now().date().isoformat()

        sb.table("purchase_orders").update(upd).eq("id", po["id"]).execute()
        log_activity(po["id"], user_name, user_role, "status_changed",
                      f"{po['status']} → {new_status}" + (f" | {note}" if note else ""))
        return True
    except Exception:
        return False


def delete_purchase_order(po_id):
    try:
        get_supabase().table("purchase_orders").delete().eq("id", po_id).execute()
        return True
    except Exception:
        return False


def get_unique_suppliers():
    try:
        r = get_supabase().table("purchase_orders").select("supplier_name").not_.is_("supplier_name", "null").execute()
        return sorted(set(x["supplier_name"] for x in (r.data or []) if x.get("supplier_name")))
    except Exception:
        return []


# --- Deliveries ---
def add_delivery(po_id, items_received, overall_condition, issue_description="",
                 notes="", image_urls=None, user_name=""):
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

        # อัปเดต status
        po = get_purchase_order(po_id)
        if po:
            new_status = "มีปัญหา" if overall_condition != "ปกติ" else "รับของแล้ว"
            sb.table("purchase_orders").update({
                "status": new_status,
                "received_date": datetime.now().date().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }).eq("id", po_id).execute()
            log_activity(po_id, user_name, "requester", "received",
                          f"รับของ #{d_no} | สภาพ: {overall_condition}")
        return delivery
    except Exception as e:
        st.error(f"บันทึกไม่สำเร็จ: {e}")
        return None


def get_deliveries(po_id):
    try:
        return get_supabase().table("po_deliveries").select("*").eq("po_id", po_id).order("delivery_no").execute().data or []
    except Exception:
        return []


# --- Activity ---
def log_activity(po_id, user_name, user_role, action, description=""):
    try:
        get_supabase().table("po_activities").insert({
            "po_id": po_id, "user_name": user_name, "user_role": user_role,
            "action": action, "description": description,
        }).execute()
        return True
    except Exception:
        return False


def get_activities(po_id):
    try:
        return get_supabase().table("po_activities").select("*").eq("po_id", po_id).order("created_at", desc=True).execute().data or []
    except Exception:
        return []


# --- Comments ---
def add_comment(po_id, user_name, user_role, message):
    try:
        get_supabase().table("po_comments").insert({
            "po_id": po_id, "user_name": user_name,
            "user_role": user_role, "message": message,
        }).execute()
        log_activity(po_id, user_name, user_role, "commented", message[:100])
        return True
    except Exception:
        return False


def get_comments(po_id):
    try:
        return get_supabase().table("po_comments").select("*").eq("po_id", po_id).order("created_at").execute().data or []
    except Exception:
        return []


# --- Notifications ---
def add_notification(user_id, po_id, title, message=""):
    try:
        get_supabase().table("notifications").insert({
            "user_id": user_id, "po_id": po_id, "title": title, "message": message,
        }).execute()
        return True
    except Exception:
        return False


def get_notifications(user_id, unread_only=False):
    try:
        q = get_supabase().table("notifications").select("*").eq("user_id", user_id)
        if unread_only:
            q = q.eq("is_read", False)
        return q.order("created_at", desc=True).limit(50).execute().data or []
    except Exception:
        return []


def mark_notification_read(nid):
    try:
        get_supabase().table("notifications").update({"is_read": True}).eq("id", nid).execute()
        return True
    except Exception:
        return False


def mark_all_notifications_read(user_id):
    try:
        get_supabase().table("notifications").update({"is_read": True}).eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


# --- Overdue/Upcoming ---
def get_overdue_pos():
    try:
        today = date.today().isoformat()
        return get_supabase().table("purchase_orders").select("*").lt("expected_date", today).in_("status", ["สั่งซื้อแล้ว", "กำลังขนส่ง"]).execute().data or []
    except Exception:
        return []


def get_upcoming_pos(days=3):
    try:
        today = date.today()
        deadline = (today + timedelta(days=days)).isoformat()
        return get_supabase().table("purchase_orders").select("*").gte("expected_date", today.isoformat()).lte("expected_date", deadline).in_("status", ["สั่งซื้อแล้ว", "กำลังขนส่ง"]).execute().data or []
    except Exception:
        return []
