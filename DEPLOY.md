# 🚀 Deployment Guide — Lab Parfumo PO Pro

คู่มือการ deploy ระบบ Lab Parfumo PO Pro ตั้งแต่เริ่มต้น — สำหรับ Supabase + Streamlit Cloud

---

## 📋 Checklist รวม

- [ ] สร้าง Supabase project + run migrations ทั้งหมด
- [ ] ตั้งค่า Supabase Storage buckets
- [ ] สร้าง admin user
- [ ] ตั้ง secrets ใน Streamlit
- [ ] Deploy โค้ดไป Streamlit Cloud (หรือ self-host)
- [ ] ทดสอบ login + create PO

---

## 1️⃣ Supabase Setup

### 1.1 สร้าง Project
1. ไปที่ https://supabase.com → **New Project**
2. ตั้ง name + password (เก็บไว้ดี)
3. รอ project พร้อม (~2 นาที)

### 1.2 รัน Migrations ตามลำดับ

⚠️ **ลำดับสำคัญ — ห้ามสลับ!**

ไปที่ **SQL Editor** ใน Supabase แล้วรันตามลำดับ:

| # | ไฟล์ | คำอธิบาย |
|---|---|---|
| 1 | `supabase_setup.sql` | Schema หลัก — users, equipment, purchase_orders, ฯลฯ |
| 2 | `migration_security.sql` | Login attempts + must_change_password |
| 3 | `migration_user_sessions.sql` | Session tokens (โต๊ะหลัก) |
| 4 | `migration_user_sessions_fix.sql` | ⭐ NEW — แก้ schema conflict |
| 5 | `migration_multi_images.sql` | Equipment.image_urls (array) |
| 6 | `migration_category_order.sql` | Display order ของ categories |
| 7 | `migration_po_drafts.sql` | Auto-save PO drafts |
| 8 | `migration_withdrawals.sql` | Stock withdrawal tracking |
| 9 | `migration_pending_equipment.sql` | Custom items ที่รออนุมัติ |
| 10 | `migration_company_settings.sql` | Company info ใน DB |
| 11 | `migration_login_intro.sql` | Customizable login intro |
| 12 | `migration_atomic_counter.sql` | ⭐ **NEW** — Race-condition-free PO num + withdrawal |
| 13 | `migration_security_v2.sql` | ⭐ **NEW** — bcrypt support + soft-delete fields |
| 14 | `migration_budget.sql` | ⭐ **NEW** — Budget tracking feature |

**วิธีรัน:**
1. SQL Editor → New Query
2. Copy ทั้งไฟล์ → paste → **Run**
3. ตรวจ output ว่าไม่มี error
4. ทำซ้ำกับไฟล์ถัดไป

### 1.3 สร้าง Storage Buckets

ไปที่ **Storage** → **New Bucket**:

| Bucket | Public? | คำอธิบาย |
|---|---|---|
| `equipment-images` | ✅ Public | รูปสินค้าใน Catalog |
| `delivery-images` | ✅ Public | รูปประกอบการรับของ |
| `po-attachments` | ✅ Public | ไฟล์แนบของ PO |

หลังสร้าง — ไปที่แต่ละ bucket → **Configuration** → ตั้ง file size limit ~10MB

---

## 2️⃣ สร้าง Admin User คนแรก

ใน SQL Editor รัน (เปลี่ยน username/password ตามต้องการ):

```sql
-- ⭐ ใหม่ใช้ bcrypt — ห้าม insert hash จาก SQL ตรงๆ ได้แล้ว!
-- วิธีที่ 1: ใช้ Python script — สร้างไฟล์ bootstrap.py แล้วรันครั้งเดียว
```

สร้างไฟล์ `bootstrap_admin.py` (ไฟล์ใช้ครั้งเดียว — ลบทิ้งหลังใช้):

```python
"""bootstrap_admin.py — สร้าง admin คนแรก
รันครั้งเดียวแล้วลบไฟล์ทิ้ง"""
import os
import bcrypt
from supabase import create_client

URL = os.environ['SUPABASE_URL']
KEY = os.environ['SUPABASE_SERVICE_ROLE_KEY']  # ⚠️ ใช้ service role!

USERNAME = "admin"
PASSWORD = "ChangeMe123"  # user จะถูกบังคับเปลี่ยนตอน login
FULL_NAME = "ผู้ดูแลระบบ"

password_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()

sb = create_client(URL, KEY)
result = sb.table("users").insert({
    "username": USERNAME,
    "password_hash": password_hash,
    "full_name": FULL_NAME,
    "role": "admin",
    "must_change_password": True,
    "is_active": True,
}).execute()

print(f"✅ Created admin: {USERNAME} / {PASSWORD}")
print("⚠️ Login แล้วระบบจะบังคับให้เปลี่ยนรหัส")
```

รัน:
```bash
pip install bcrypt supabase
SUPABASE_URL="..." SUPABASE_SERVICE_ROLE_KEY="..." python bootstrap_admin.py
```

หลัง login ครั้งแรก → ลบไฟล์ `bootstrap_admin.py` ทิ้ง

---

## 3️⃣ Secrets Configuration

### 3.1 Streamlit Secrets

สร้างไฟล์ `.streamlit/secrets.toml`:

```toml
# Supabase
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGc..."

# Email (optional — ดู SMTP_SETUP.md)
[email]
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "app-password"  # ใช้ App Password ของ Gmail
FROM_EMAIL = "your-email@gmail.com"
FROM_NAME = "Lab Parfumo PO"

# LINE Notify (optional)
[line]
LINE_TOKEN = ""

# Webhook (optional)
[webhook]
WEBHOOK_URL = ""
```

### 3.2 ใน Streamlit Cloud
ไปที่ App settings → **Secrets** → paste เนื้อหาจาก `secrets.toml`

---

## 4️⃣ Bootstrap Defaults (Optional)

ใน SQL Editor รัน — สร้างหมวดหมู่เริ่มต้น:

```sql
INSERT INTO equipment_categories (name, display_order)
VALUES 
    ('ขวดบรรจุ', 1),
    ('ฝา/จุก', 2),
    ('กล่องบรรจุภัณฑ์', 3),
    ('สติกเกอร์/ฉลาก', 4),
    ('อุปกรณ์อื่นๆ', 5)
ON CONFLICT DO NOTHING;
```

ตั้งข้อมูลบริษัท (หรือทำผ่านหน้า Settings ในระบบ):
```sql
INSERT INTO company_settings (id, name, name_th, tax_id, website)
VALUES (1, 'Lab Parfumo', 'บริษัท ทัช ไดเวอร์เจนซ์ จำกัด', '0115564002651', 'www.labparfumo.com')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    name_th = EXCLUDED.name_th;
```

---

## 5️⃣ Deploy

### 5.1 Streamlit Cloud (แนะนำ)
1. Push โค้ดไป GitHub
2. ไปที่ https://share.streamlit.io
3. **New app** → เลือก repo + branch
4. Main file: `app.py`
5. Advanced → Python version: **3.11** (หรือ 3.12)
6. Secrets — paste จาก step 3.2
7. **Deploy!**

### 5.2 Self-host (Docker / VM)

ใช้ `requirements.txt` (ที่อัปเดตแล้ว — มี bcrypt):

```bash
# Ubuntu — ต้องติดตั้ง weasyprint dependencies ก่อน
sudo apt-get install -y libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# Install Python deps
pip install -r requirements.txt

# Run
streamlit run app.py --server.port 8501
```

⚠️ **สำคัญ:** ติดตั้งฟอนต์ Sarabun ใน folder `fonts/`:
- Download: https://github.com/google/fonts/tree/main/ofl/sarabun
- Copy `Sarabun-Regular.ttf` + `Sarabun-Bold.ttf` ไปที่ `fonts/`
- ถ้าไม่ใส่ฟอนต์ → PDF ภาษาไทยจะแสดงผิด

---

## 6️⃣ Migration จากเวอร์ชันก่อนหน้า

### Upgrade จาก v1 (SHA-256 password)

หากมี user เก่าที่ใช้ SHA-256 อยู่แล้ว:

1. **ไม่ต้องลบ user หรือบังคับ reset** — code ใหม่ตรวจรหัสได้ทั้ง 2 format
2. ตอน user login ครั้งถัดไป — code จะ auto-upgrade hash เป็น bcrypt **ทันที** โดย user ไม่รู้ตัว
3. ทำการตรวจหลัง 1 เดือน:

```sql
-- ตรวจว่าเหลือ user ที่ยังใช้ SHA-256 อยู่ไหม
SELECT username, full_name, last_login_at,
    CASE 
        WHEN password_hash LIKE '$2%' THEN '✅ bcrypt'
        WHEN length(password_hash) = 64 THEN '⚠️ legacy SHA-256'
        ELSE '❌ unknown'
    END AS hash_format
FROM users
WHERE is_active = true
ORDER BY last_login_at DESC;
```

ถ้ามี user ที่ยังเป็น SHA-256 = user คนนั้นไม่ได้ login เลย → consider deactivate หรือ contact

---

## 7️⃣ Health Check

หลัง deploy เรียบร้อย — ตรวจ:

| ✅ | Test | คำอธิบาย |
|---|---|---|
| ☐ | Login as admin | username/password ที่สร้างใน step 2 |
| ☐ | บังคับเปลี่ยนรหัส | ระบบควรพาไปหน้าตั้งรหัสใหม่ |
| ☐ | สร้าง user ใหม่ | Settings → Users → ➕ |
| ☐ | สร้าง equipment + category | Catalog → ➕ |
| ☐ | สร้าง PO + ดู PDF | สร้าง → ดาวน์โหลด PDF — ตรวจภาษาไทย |
| ☐ | Withdraw stock | ทดลองเบิก — stock ลดลงถูกต้อง |
| ☐ | ดู Activity log | History ของ PO ครบ |
| ☐ | Budget tracking | ตั้งงบ → สร้าง PO → ดู % ใช้ไป |
| ☐ | Period PDF report | Generate รายงานเดือนนี้ |

---

## 🆘 Troubleshooting

### "supabase config not found"
- ตรวจ secrets.toml มี `SUPABASE_URL` + `SUPABASE_ANON_KEY`
- ถ้า self-host — ตั้ง env vars `SUPABASE_URL` + `SUPABASE_ANON_KEY`

### "Cannot create PO" / "Username already exists"
- ตรวจ migrations ครบทุกไฟล์ตามตาราง
- ตรวจ `counters` table มี data — ถ้าไม่มี migration_atomic_counter จะหา function `next_po_number` ไม่เจอ

### "PDF ภาษาไทยเป็นกล่อง"
- ฟอนต์ `Sarabun-Regular.ttf` + `Sarabun-Bold.ttf` ต้องอยู่ใน `fonts/`
- ตรวจสิทธิ์ไฟล์ — Streamlit Cloud ต้อง read ได้

### "Login fail หลัง upgrade"
- ตรวจว่ารัน migration_security_v2.sql แล้ว
- รัน query ตรวจ password format (ดูใน step 6)
- ตรวจว่าติดตั้ง `bcrypt>=4.0.0` แล้ว (`pip list | grep bcrypt`)

### Race condition ยังเกิด (PO เลขซ้ำ)
- ตรวจว่ารัน migration_atomic_counter.sql แล้ว:
  ```sql
  SELECT proname FROM pg_proc WHERE proname IN ('next_po_number', 'withdraw_stock');
  ```
- ผลควรได้ 2 rows

---

## 📞 Contact

หากพบปัญหาเพิ่มเติม — เปิด issue ที่ GitHub repo
