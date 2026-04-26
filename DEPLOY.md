# 🚀 Lab Parfumo PO Pro — Deployment Guide

## 📋 Overview

Streamlit + Supabase + WeasyPrint app deployed on Streamlit Cloud.

## 🏗️ Architecture
- **Frontend:** Streamlit (Python)
- **Database:** Supabase (PostgreSQL + Storage)
- **PDF Generation:** WeasyPrint + Sarabun font
- **Hosting:** Streamlit Cloud (FREE tier)

---

## 📦 Step 1: Setup Supabase

### 1.1 Create Project
- Go to https://supabase.com → New Project
- Region: Singapore (closest to Thailand)
- DB Password: บันทึกไว้

### 1.2 รัน SQL Migrations ตามลำดับ
ใน **SQL Editor → New query → Run** ทีละไฟล์:

1. **`supabase_setup.sql`** — สร้างตารางหลัก
2. **`migration_security.sql`** — login attempt + lockout
3. **`migration_user_sessions.sql`** — Session persistence
4. **`migration_multi_images.sql`** — รูปหลายรูป
5. **`migration_category_order.sql`** — จัดลำดับหมวด
6. **`migration_po_drafts.sql`** — Auto-save draft PO
7. **`migration_withdrawals.sql`** — ระบบเบิกสินค้า
8. **`migration_pending_equipment.sql`** — Approval flow

### 1.3 สร้าง Storage Buckets (Public)
- `equipment-images`
- `delivery-images`
- `po-attachments`

---

## 🌐 Step 2: Deploy บน Streamlit Cloud

### 2.1 Push code ไป GitHub
- สร้าง repo (Private แนะนำ)
- Upload ทุกไฟล์ใน `po_pro/`
- ❌ **อย่าใส่** `secrets.toml` ใน repo

### 2.2 Deploy
- https://share.streamlit.io → New app → เลือก repo
- Main file: `app.py`
- **Secrets:**
  ```toml
  [supabase]
  url = "https://YOUR-PROJECT.supabase.co"
  anon_key = "YOUR-ANON-KEY"
  
  [app]
  base_url = "https://YOUR-APP.streamlit.app"
  ```

### 2.3 รอ Build (~3-5 นาที)

---

## 🔑 Step 3: Initial Setup

### Default Accounts
- **admin / admin123** (admin)
- **staff1 / staff123** (requester)

⚠️ **เปลี่ยนรหัสทันทีครั้งแรกที่ login!**

---

## 🔄 Update Workflow

### Edit บน GitHub:
1. คลิกไฟล์ → ✏️ Edit → Cmd+A → Delete → Paste → Commit
2. Streamlit Cloud rebuild อัตโนมัติ (1-2 นาที)

### ลำดับสำคัญ:
1. SQL migrations ก่อน (Supabase)
2. `requirements.txt` (ถ้ามี dep ใหม่)
3. รอ rebuild
4. Code files

---

## 📊 Features

### สำหรับทุกคน
- 📊 Dashboard + smart alerts
- 📝 สร้าง PO + auto-save draft + upload รูป
- 📤 เบิกสินค้า + Export CSV/Excel
- 📦 รอรับของ
- 🔔 Notifications
- 🔍 Global search

### สำหรับ Admin
- 🛒 สั่งซื้อ + กรอกราคา
- 📂 จัดการ Catalog + หมวด
- ✅ Approve สินค้าใหม่ที่ user เสนอ
- 📈 รายงาน + Quick insights
- 👥 จัดการ users

### Notifications (อัตโนมัติ)
| Event | ใครได้รับ |
|---|---|
| Staff สร้าง PO | Admin ทุกคน |
| PO ค้าง > 3 วัน | Admin (ทุกวัน) |
| Admin สั่งซื้อ | ผู้สร้าง PO |
| Tracking อัปเดต | ผู้สร้าง PO |
| รับของ / มีปัญหา | Admin |
| ปิดงาน / ยกเลิก | ทุกฝ่าย |

---

## 🛠️ Troubleshooting

### "secrets not found"
- เช็ค Streamlit Cloud → Settings → Secrets ครบไหม

### PDF ไทยเป็นช่อง
- เช็ค `fonts/Sarabun-*.ttf` upload ครบ
- เช็ค `packages.txt` มี `libpango-1.0-0` + `libpangoft2-1.0-0`

### Login แล้ว Refresh หาย
- ตรวจ `migration_user_sessions.sql` รันแล้ว

### รูปไม่ขึ้น
- Storage buckets ต้องเป็น **Public**
