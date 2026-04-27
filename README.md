# 📦 ไฟล์ทั้งหมดสำหรับ Lab Parfumo PO

> **Update: 27 เม.ย. 2026** — ครบทุกไฟล์ที่ต้องการ

---

## 📂 ไฟล์ในแพ็คนี้ (10 ไฟล์)

### 🐍 Python files (6 ไฟล์)

| ไฟล์ | ขนาด | วิธี Upload |
|---|---|---|
| `app.py` ⭐ | 64KB | **Replace ทับของเดิม** (มี Budget แล้ว) |
| `helpers.py` | 9KB | **Replace ทับของเดิม** |
| `database.py` | 70KB | **Replace ทับของเดิม** |
| `pdf_generator.py` | 28KB | **Replace ทับของเดิม** |
| `pages_budget.py` | 20KB | ใหม่ — มีอยู่แล้ว skip ได้ |
| `requirements.txt` | 1KB | **Replace ทับของเดิม** |

### 🗄️ SQL Migrations (4 ไฟล์)

ถ้ารันใน Supabase แล้วครบ — **ข้ามไฟล์เหล่านี้ได้**

| ไฟล์ | ใช้ทำอะไร |
|---|---|
| `migration_user_sessions_fix.sql` | แก้ schema |
| `migration_atomic_counter.sql` | Race condition fix |
| `migration_security_v2.sql` | bcrypt support |
| `migration_budget.sql` | Budget feature |

---

## 🚀 วิธี Upload เข้า GitHub (ง่ายสุด)

### Step 1: Download ไฟล์ทั้งหมด

1. คลิกที่ **ZIP file** ที่ผมส่งให้
2. ไฟล์ลงที่ `~/Downloads/`
3. **Double-click** ที่ ZIP → extract เป็น folder

### Step 2: Upload ทับเข้า GitHub

1. เปิด: https://github.com/anavin/lab-parfumo-po
2. คลิกปุ่ม **`Add file`** (มุมขวาบน — สีขาว)
3. เลือก **`Upload files`**
4. **ลาก-วางไฟล์ทั้งหมด** จาก folder ที่ extract เข้าไป
   - เลือกได้ทั้ง 6 ไฟล์ Python
   - หรือเลือกแค่ที่ต้องการ
5. GitHub จะถาม "Replace existing files?" → **คลิก Yes** สำหรับทุกไฟล์
6. เลื่อนลงล่าง → ใส่ commit message:
   ```
   Update all files - Add Budget feature + security patches
   ```
7. คลิกปุ่มสีเขียว **`Commit changes`**

### Step 3: รอ Streamlit Cloud deploy

- รอ 2-3 นาที
- เปิด app → กด `Cmd + Shift + R` (Refresh)
- คลิก **🛠️ เครื่องมือ ▾** → ควรเห็น **💰 งบ**

---

## ✅ สิ่งที่ผมแก้ใน `app.py`

แค่ 2 จุด — เพิ่ม Budget feature:

### จุดที่ 1 (บรรทัด ~915):
```python
admin_modes = [
    ('equipment', '📦 Catalog'),
    ('budget', '💰 งบ'),          ⬅️ เพิ่มใหม่
    ('reports', '📈 รายงาน'),
    ...
]
```

### จุดที่ 2 (บรรทัด ~1693):
```python
elif mode == 'budget':                       ⬅️ เพิ่ม block
    if not is_admin():                       
        st.error("❌ เฉพาะแอดมิน")
        return
    from pages_budget import render_budget
    render_budget()
elif mode == 'reports':
    ...
```

---

## 📊 ขนาดไฟล์ตรวจสอบ

ก่อน upload — ตรวจขนาดไฟล์ใน Finder:

| ไฟล์ | ขนาดที่ถูกต้อง |
|---|---|
| `app.py` | ~64-66 KB |
| `helpers.py` | ~9-10 KB |
| `database.py` | ~70-72 KB |
| `pdf_generator.py` | ~28-29 KB |
| `pages_budget.py` | ~20-21 KB |
| `requirements.txt` | < 1 KB |

ถ้าขนาดต่างกันมาก = อาจมีปัญหา → ลอง download อีกที

---

## 🆘 ถ้ามีปัญหา

### ❌ "Cannot upload file because it already exists"
→ GitHub ขอให้ replace — คลิก **`Replace`** หรือ **`Overwrite`**

### ❌ "App error" หลัง deploy
1. ดู Streamlit Cloud logs
2. Screenshot ส่งให้ผม

### ❌ "ไม่เห็นเมนู 💰 งบ"
1. กด `Cmd + Shift + R` (refresh แรง)
2. Logout แล้ว login ใหม่
3. ถ้ายังไม่เห็น → ตรวจว่า `pages_budget.py` อยู่ใน GitHub แล้ว

---

ส่ง screenshot หลัง upload เสร็จ — ผมจะ verify ให้ครับ 🛠️
