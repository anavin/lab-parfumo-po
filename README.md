# 📦 Lab Parfumo PO Pro System

ระบบบันทึกใบสั่งซื้ออุปกรณ์บรรจุภัณฑ์ภายในองค์กร — แบบมืออาชีพ
สร้างด้วย Python + Streamlit + Supabase

---

## ✨ ฟีเจอร์หลัก

### 👥 Multi-Role
- **ผู้สั่ง (Requester)** — สร้างใบ PO, ติดตามสถานะ, รับของ (❌ ไม่เห็นราคา/supplier)
- **แอดมิน + จัดซื้อ (Admin)** — เห็นทุกอย่าง, จัดการระบบ, ออก PO ส่ง supplier

### 🔄 Workflow 7 สถานะ
```
📝 รอจัดซื้อดำเนินการ → ✅ สั่งซื้อแล้ว → 🚚 กำลังขนส่ง 
                  → 📦 รับของแล้ว → ✓ เสร็จสมบูรณ์
                                    ↓
                              ⚠️ มีปัญหา (ถ้ามี)
                                    
                              ❌ ยกเลิก (ตลอดเวลา)
```

### 📊 Dashboard อัจฉริยะ
- KPI metrics ตาม role
- Alert: PO เลยกำหนด + ใกล้ครบกำหนด
- งานที่ต้องดำเนินการ
- ภาพรวมสถานะทั้งหมด

### 📝 ใบ PO
- **ผู้สั่ง:** กรอกแค่ชื่อสิ่งที่ต้องการ + จำนวน + เหตุผล
- **จัดซื้อ:** กรอกข้อมูล supplier + ราคา + วันที่คาดได้รับ
- หลายรายการในใบเดียว
- เลขที่อัตโนมัติ (PO-2026-0001)

### 📦 รับของ (พร้อมรายละเอียด)
- จำนวนที่ได้รับจริง vs สั่ง
- จำนวนเสียหาย + หมายเหตุ
- อัปโหลดรูปได้หลายรูป
- บันทึกหลายรอบ (กรณีของมาเป็นล็อต)
- สร้างใบรับของ (GRN) PDF

### 🔔 แจ้งเตือน 3 ช่องทาง
- **In-app** — แสดงในหน้าแอป + badge จำนวน
- **อีเมล** — Gmail SMTP (ตั้งค่าใน secrets)
- **LINE Notify / Webhook** — Discord/Slack/อื่นๆ

### 📈 รายงาน (Admin)
- ตัวกรองช่วงเวลา
- สรุปตาม Supplier / รายการ
- Export CSV

### 💬 ทีมเวิร์ก
- Comments ในใบ PO
- Activity log (audit trail)
- ติดตามได้ว่าใครทำอะไรเมื่อไหร่

### 📄 PDF
- **ใบ PO** สำหรับส่ง supplier (เห็นเฉพาะ admin)
- **ใบรับของ (GRN)** พร้อมรูป + รายละเอียดสภาพ

---

## 🔐 บัญชีเริ่มต้น

```
admin / admin123     → แอดมิน + จัดซื้อ
staff1 / staff123    → ผู้สั่ง
```

⚠️ **ควรเปลี่ยนรหัสผ่านทันทีหลังใช้ครั้งแรก** — ไปที่เมนู "👥 ผู้ใช้"

---

## 📁 โครงสร้างไฟล์

```
po_pro/
├── app.py                  ← main + login + dashboard
├── helpers.py              ← shared helpers
├── pages_po.py             ← PO list/create/view/procure/receive
├── pages_admin.py          ← equipment/reports/users/notifications
├── database.py             ← Supabase wrapper
├── pdf_generator.py        ← PDF (PO + GRN)
├── notify.py               ← Email/LINE/Webhook
├── supabase_setup.sql      ← SQL schema
├── requirements.txt
├── run.sh / run.bat
├── DEPLOY.md               ← คู่มือ deploy ⭐
└── .streamlit/
    └── secrets.toml.example
```

---

## 🚀 Quick Start

ดูคู่มือเต็มใน **`DEPLOY.md`** — ใช้เวลาตั้งค่า ~30 นาที

### Local
```bash
chmod +x run.sh
./run.sh
```

### Cloud (Streamlit Cloud + Supabase) - แนะนำ!
ดู `DEPLOY.md` ทำตาม 3 phases:
1. ตั้ง Supabase (15 นาที)
2. ตั้ง local config (5 นาที)
3. Deploy ขึ้น Streamlit Cloud (10 นาที)

---

**Version 2.0 Pro** — Lab Parfumo PO System
