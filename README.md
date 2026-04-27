# 📦 ไฟล์ทั้งหมดสำหรับอัพ GitHub

> **Update: 27 เม.ย. 2026**

---

## 📂 โครงสร้างไฟล์

```
lab-parfumo-patches/
├── python-files/           ← ใส่ใน root ของ repo
│   ├── helpers.py          ← REPLACE ไฟล์เดิม
│   ├── database.py         ← REPLACE ไฟล์เดิม
│   ├── pdf_generator.py    ← REPLACE ไฟล์เดิม
│   ├── requirements.txt    ← REPLACE ไฟล์เดิม
│   └── pages_budget.py     ← NEW (ไฟล์ใหม่)
│
└── migrations/             ← รันใน Supabase SQL Editor
    ├── migration_user_sessions_fix.sql
    ├── migration_atomic_counter.sql
    ├── migration_security_v2.sql
    └── migration_budget.sql
```

---

## ✅ Checklist อัพ GitHub

### 1. Replace ไฟล์เดิม (4 ไฟล์)

ใน github.dev → คลิกแต่ละไฟล์ → ลบเนื้อหาเดิม → Paste ของใหม่

- [ ] `helpers.py` 
- [ ] `database.py`
- [ ] `pdf_generator.py`
- [ ] `requirements.txt`

### 2. เพิ่มไฟล์ใหม่ (1 ไฟล์)

ใน github.dev → คลิกขวาที่ file tree → New File

- [ ] `pages_budget.py`

### 3. แก้ `app.py` 2 จุด (manual)

**จุดที่ 1:** หา `admin_modes = [` → เพิ่ม:
```python
('budget', '💰 งบ'),
```
ระหว่าง `('equipment', '📦 Catalog'),` และ `('reports', '📈 รายงาน'),`

**จุดที่ 2:** หา `elif mode == 'reports':` → เพิ่มก่อนหน้า:
```python
    elif mode == 'budget':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        from pages_budget import render_budget
        render_budget()
```

### 4. Save + Commit + Push

- กด `Cmd + S` ทุกไฟล์
- คลิก 🌿 Source Control
- ใส่ commit message: `Apply security patches + Budget feature`
- กด **Commit**
- กด **Sync Changes** (ถ้าไม่ auto-push)

### 5. รัน SQL ใน Supabase (4 ไฟล์ตามลำดับ)

ใน https://supabase.com/dashboard/project/xsincbyvnvchwkddhidt/sql

ลำดับสำคัญ! ห้ามสลับ:

- [ ] **1.** `migration_user_sessions_fix.sql`
- [ ] **2.** `migration_atomic_counter.sql`
- [ ] **3.** `migration_security_v2.sql`
- [ ] **4.** `migration_budget.sql`

---

## 🔍 ตรวจหลัง Upload

เปิด https://github.com/anavin/lab-parfumo-po → ตรวจว่ามีไฟล์ครบ:

- [ ] `pages_budget.py` ✅
- [ ] `helpers.py` (ขนาด ~9KB)
- [ ] `database.py` (ขนาด ~70KB)
- [ ] `pdf_generator.py` (ขนาด ~28KB)
- [ ] `requirements.txt` มีคำว่า `bcrypt` ข้างใน

---

## 🧪 ทดสอบหลัง Streamlit Cloud deploy

1. รอ 2-5 นาที (Streamlit auto-deploy)
2. เปิด app → Login admin
3. ดูเมนู `🛠️ เครื่องมือ ▾` → ควรมี **💰 งบ** ใหม่
4. คลิก 💰 งบ → เห็น 3 tabs

---

## ❌ ถ้า App Error หลัง Deploy

**Error ที่พบบ่อย:**

| Error | สาเหตุ | วิธีแก้ |
|---|---|---|
| `ModuleNotFoundError: bcrypt` | requirements.txt ไม่มี bcrypt | ตรวจ requirements.txt |
| `SyntaxError in app.py` | Indent ผิด | กลับไปแก้ app.py |
| `ImportError: render_budget` | ไฟล์ pages_budget.py ผิดพลาด | ตรวจไฟล์ |
| `function next_po_number does not exist` | ลืมรัน SQL migration | รัน migration_atomic_counter.sql |

---

ส่ง screenshot/error message ให้ผมถ้าติด — จะช่วยแก้ทันทีครับ! 🛠️
