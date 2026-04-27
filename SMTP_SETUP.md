# 📧 Setup Email Notification (Gmail SMTP)

ตั้งค่า Gmail SMTP เพื่อให้ระบบ Lab Parfumo PO Pro ส่งอีเมลแจ้งเข้าใช้งานได้

## 🔧 ขั้นตอนที่ 1: เปิด App Password ของ Gmail

Gmail ไม่อนุญาต login ด้วย password ตรงๆ — ต้องสร้าง "App Password" แยก

### วิธีสร้าง:

1. ไปที่ https://myaccount.google.com/security
2. เปิด **2-Step Verification** ก่อน (ถ้ายังไม่ได้เปิด — ระบบ App Password ต้องการ)
3. ค้นหา "App Passwords" หรือไปที่ https://myaccount.google.com/apppasswords
4. กรอกชื่อ app เช่น `Lab Parfumo PO Pro` → คลิก Create
5. **Copy รหัส 16 หลัก** (เช่น `abcd efgh ijkl mnop`) — รหัสนี้แสดงครั้งเดียว!

## 🔧 ขั้นตอนที่ 2: ตั้งค่าใน Streamlit Cloud

1. เข้า https://share.streamlit.io
2. คลิก app `lab-parfumo-po`
3. Settings → **Secrets**
4. เพิ่ม secrets ตามนี้:

```toml
# Gmail SMTP
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USERNAME = "labparfumo@gmail.com"
SMTP_PASSWORD = "abcd efgh ijkl mnop"
SMTP_FROM = "Lab Parfumo PO Pro <labparfumo@gmail.com>"

# URL ของแอป (ใช้ในลิงก์อีเมล)
APP_URL = "https://your-app-name.streamlit.app"
```

5. คลิก **Save**
6. รอแอป restart (~30 วินาที)

## 🧪 ทดสอบ

1. Login เป็น admin
2. ไปที่ **🛠️ เครื่องมือ → 👥 จัดการผู้ใช้**
3. ลอง **➕ เพิ่มผู้ใช้ใหม่**
4. ใส่อีเมลของตัวเอง (สำหรับทดสอบ)
5. ☑️ "ส่งอีเมลแจ้ง user เพื่อเข้าใช้งานครั้งแรก"
6. ✅ เพิ่ม → ตรวจอีเมล (รวม Spam folder)

## ⚠️ Troubleshooting

### ส่งอีเมลไม่ได้ — "ไม่สามารถส่งอีเมลได้ — ตรวจสอบการตั้งค่า SMTP"

**สาเหตุที่เป็นไปได้:**
1. **2-Step Verification ยังไม่เปิด** → เปิดที่ Google Security
2. **App Password ผิด** → สร้างใหม่ + paste อีกครั้งใน Streamlit Secrets
3. **อีเมลผิด format** ใน SMTP_FROM → ใช้ `Display Name <email@domain.com>`
4. **Streamlit ยังไม่ restart** → save secrets อีกครั้ง รอ 1 นาที

### อีเมลเข้า Spam

แก้:
- ใน SMTP_FROM ใช้ display name ชัดเจน (เช่น `"Lab Parfumo PO <...>"`)
- ส่งอีเมลทดสอบจาก labparfumo@gmail.com ไปยัง user แล้วให้ user
  คลิก "Not Spam" ครั้งแรก

## 🔐 ข้อจำกัด Gmail SMTP

- 500 emails/วัน (พอใช้ — ปกติเพิ่ม user ไม่บ่อย)
- ถ้า user เยอะ (>500/วัน) แนะนำใช้ **Resend** หรือ **SendGrid** แทน

## 🔄 ใช้ Resend แทน (ทางเลือก)

ถ้าจะใช้ Resend (ฟรี 3,000 emails/เดือน) — ตั้งค่าเป็น SMTP:

```toml
SMTP_HOST = "smtp.resend.com"
SMTP_PORT = "587"
SMTP_USERNAME = "resend"
SMTP_PASSWORD = "re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SMTP_FROM = "Lab Parfumo <onboarding@resend.dev>"
```

(สมัครและขอ API key ที่ https://resend.com)
