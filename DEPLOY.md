# 🚀 คู่มือ Deploy Lab Parfumo PO Pro

ทำตามขั้นตอนนี้เพื่อให้ระบบใช้งานได้ — ใช้เวลา ~30 นาที

---

# Phase 1: ตั้งค่า Supabase (~15 นาที)

## 1.1 สมัคร Supabase
1. ไปที่ https://supabase.com → **Start your project**
2. **Sign in with GitHub**

## 1.2 สร้าง Project
1. กด **New project**
2. กรอก:
   - **Name:** `lab-parfumo-po`
   - **Database Password:** ตั้งรหัสและเก็บไว้
   - **Region:** **Southeast Asia (Singapore)**
   - **Plan:** Free
3. รอประมาณ 2 นาที

## 1.3 รัน SQL สร้างตาราง
1. เมนูซ้าย → **SQL Editor** → **New query**
2. เปิดไฟล์ `supabase_setup.sql` คัดลอกทั้งหมด → วาง → กด **Run**
3. เห็น "Success" = สำเร็จ ✅

## 1.4 สร้าง Storage Buckets (2 ตัว)

### Bucket #1: equipment-images
1. เมนูซ้าย → **Storage** → **New bucket**
2. **Name:** `equipment-images` (ขีดกลาง)
3. ✅ **Public bucket**
4. **Save**

### Bucket #2: delivery-images
1. **New bucket** อีกครั้ง
2. **Name:** `delivery-images`
3. ✅ **Public bucket**
4. **Save**

## 1.5 ตั้ง Storage Policies (ทั้ง 2 buckets)

ทำเหมือนกันทั้ง 2 bucket:

1. คลิก bucket → **Policies** → **New policy** → **For full customization**
2. สร้าง 2 policies:
   - **Policy 1:** Name = `Allow read`, Operation = ✅ SELECT, Target = `anon`
   - **Policy 2:** Name = `Allow upload`, Operation = ✅ INSERT, ✅ DELETE, Target = `anon`

## 1.6 คัดลอก URL + API Key
1. เมนูซ้าย → **Settings** → **API**
2. คัดลอกเก็บไว้:
   - **Project URL** (เช่น `https://xxxxx.supabase.co`)
   - **anon / public key** (เริ่มด้วย `eyJhbGc...`)

⚠️ **อย่าใช้ service_role key**

---

# Phase 2: Setup ในเครื่อง (Local)

## 2.1 แตก ZIP
```bash
unzip LabParfumoPO_Pro.zip
cd po_pro
```

## 2.2 ติดตั้ง System Dependencies (สำหรับ WeasyPrint)

### macOS
```bash
brew install pango libffi
```

### Ubuntu/Debian
```bash
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0
```

### Windows
- ดาวน์โหลด GTK3 runtime: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
- ติดตั้งและรีสตาร์ทเครื่อง

(WeasyPrint ใช้สำหรับ render PDF ภาษาไทยให้สมบูรณ์ — สระ/วรรณยุกต์อยู่ที่ถูกต้อง)

## 2.3 ตั้ง secrets
```bash
cd .streamlit
cp secrets.toml.example secrets.toml
```

แก้ `secrets.toml` ใส่ค่า Supabase:
```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGc..."
```

## 2.3 รัน
```bash
cd ..
chmod +x run.sh
./run.sh
```
(Windows: ดับเบิลคลิก `run.bat`)

Browser จะเปิดที่ `http://localhost:8501`

## 2.4 Login ครั้งแรก
- ใช้บัญชี `admin / admin123`
- **เปลี่ยนรหัสทันที** ที่เมนู "👥 ผู้ใช้"

---

# Phase 3: Deploy ขึ้น Streamlit Cloud (~10 นาที)

## 3.1 สร้าง GitHub Repo
1. https://github.com/new
2. **Name:** `lab-parfumo-po-pro`
3. ✅ **Private**
4. Create

## 3.2 อัปโหลดไฟล์
อัปโหลด **ทั้งหมด** ยกเว้น `secrets.toml`:
- `app.py`, `helpers.py`, `pages_po.py`, `pages_admin.py`
- `database.py`, `pdf_generator.py`, `notify.py`
- `requirements.txt`, `packages.txt`, `supabase_setup.sql`
- `fonts/` (โฟลเดอร์ฟอนต์ — สำคัญสำหรับ PDF ภาษาไทย!)
- `.gitignore`, `README.md`, `DEPLOY.md`
- `.streamlit/secrets.toml.example`

❌ **ห้ามอัปโหลด** `secrets.toml`

## 3.3 Deploy
1. https://share.streamlit.io → Sign in with GitHub
2. ✅ **Grant access to private repositories**
3. **New app**:
   - Repository: `your-username/lab-parfumo-po-pro`
   - Branch: `main`
   - Main file: `app.py`
4. **Advanced settings...** → ใน Secrets วาง:
```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGc..."

# ถ้าต้องการแจ้งเตือน
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your@gmail.com"
SMTP_PASSWORD = "16-digit-app-password"
SMTP_FROM = "your@gmail.com"
```
5. **Save** → **Deploy!**

รอ 3-5 นาที — ได้ URL เช่น `https://lab-parfumo-po-pro.streamlit.app`

---

# Phase 4: ตั้งค่าการแจ้งเตือน (Optional)

## 📧 Email (Gmail)
1. เปิด 2-Step Verification ที่ Google Account → Security
2. Generate App Password → ได้รหัส 16 หลัก
3. ใส่ใน secrets:
```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your@gmail.com"
SMTP_PASSWORD = "abcd efgh ijkl mnop"
SMTP_FROM = "your@gmail.com"
```
4. ใส่อีเมลให้แต่ละ user ที่หน้า "👥 ผู้ใช้"

## 📱 LINE Notify
⚠️ LINE Notify จะหยุดบริการ — แนะนำใช้ webhook แทน

## 🪝 Webhook (Discord)
1. Server → Server Settings → Integrations → Webhooks → New Webhook
2. คัดลอก Webhook URL
3. ใส่ใน secrets:
```toml
NOTIFICATION_WEBHOOK = "https://discord.com/api/webhooks/..."
```

## 🪝 Webhook (Slack)
1. https://api.slack.com/apps → Create New App
2. Incoming Webhooks → Activate → Add New Webhook
3. คัดลอก URL → ใส่ใน secrets

---

# 🆘 Troubleshooting

**Q: เปิดแอปแล้วขึ้น "ไม่พบ Supabase config"**
- ตรวจ `.streamlit/secrets.toml` ว่ามี `SUPABASE_URL` และ `SUPABASE_ANON_KEY`

**Q: Login ไม่ผ่าน**
- ตรวจว่า run SQL สำเร็จ (ดูใน Table Editor มี users table ไหม)
- ใช้บัญชี default `admin/admin123`

**Q: รูปไม่อัปโหลด**
- ตรวจ Phase 1.4 — bucket ทั้ง 2 ตัวเป็น Public
- ตรวจ Phase 1.5 — มี policies ครบ

**Q: ไม่ได้รับอีเมลแจ้งเตือน**
- ตรวจ App Password ของ Gmail (16 หลัก)
- ตรวจว่าใส่อีเมลให้ user ในหน้า "👥 ผู้ใช้"
- ดู logs ใน Streamlit Cloud

**Q: เปลี่ยนรหัสผ่านยังไง**
- เข้าเมนู "👥 ผู้ใช้" → ✏️ แก้ไข → ใส่รหัสใหม่ → 💾

**Q: เพิ่มผู้ใช้ใหม่**
- เมนู "👥 ผู้ใช้" → ➕ เพิ่มผู้ใช้ใหม่
- เลือก role: ผู้สั่ง / แอดมิน

---

# 🎯 เสร็จแล้ว!

ตอนนี้คุณมี:
- ✅ ระบบ PO Pro แบบ multi-role พร้อมใช้
- ✅ ข้อมูลปลอดภัยใน Supabase
- ✅ ใช้งานได้ทุกที่ผ่าน internet
- ✅ แจ้งเตือนหลายช่องทาง
- ✅ ฟรีทั้งหมด!

ถ้าเจอปัญหา ดู Troubleshooting ก่อน 🙂
