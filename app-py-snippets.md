# 📝 Code ที่ต้องเพิ่มใน app.py

> **คัดลอก code ด้านล่างไปใส่ใน `app.py`** — ห้ามลบของเดิม แค่เพิ่ม 2 จุด

---

## 📍 จุดที่ 1: เพิ่ม Budget ในเมนู Admin

### หาบรรทัดนี้ใน app.py

ใช้ `Cmd + F` (Find) → พิมพ์: `admin_modes = [`

### โค้ดปัจจุบัน (ของเดิม)

```python
        admin_modes = [
            ('equipment', '📦 Catalog'),
            ('reports', '📈 รายงาน'),
            ('users', '👥 ผู้ใช้'),
            ('settings', '⚙️ ตั้งค่า'),
        ]
```

### เปลี่ยนเป็น (เพิ่ม 1 บรรทัด)

```python
        admin_modes = [
            ('equipment', '📦 Catalog'),
            ('budget', '💰 งบ'),
            ('reports', '📈 รายงาน'),
            ('users', '👥 ผู้ใช้'),
            ('settings', '⚙️ ตั้งค่า'),
        ]
```

⚠️ **บรรทัดใหม่ที่เพิ่ม:** `            ('budget', '💰 งบ'),`
(ต้องมี space 12 ตัวข้างหน้า — เหมือนบรรทัดอื่นๆ)

---

## 📍 จุดที่ 2: เพิ่ม Budget ใน mode routing

### หาบรรทัดนี้ใน app.py

ใช้ `Cmd + F` → พิมพ์: `elif mode == 'reports':`

### โค้ดปัจจุบัน (ของเดิม)

```python
    elif mode == 'reports':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_reports()
```

### เปลี่ยนเป็น (เพิ่ม block ก่อนหน้า)

```python
    elif mode == 'budget':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        from pages_budget import render_budget
        render_budget()
    elif mode == 'reports':
        if not is_admin():
            st.error("❌ เฉพาะแอดมิน")
            return
        render_reports()
```

⚠️ **บล็อกใหม่ที่เพิ่ม 6 บรรทัด** — เริ่มต้นที่ `elif mode == 'budget':`

---

## ⚠️ คำเตือนเรื่อง Indent

Python ใช้ space ข้างหน้าเป็น syntax — ผิดเล็กน้อยก็ error ทันที

**ตรวจให้ดี:**
- `elif mode == 'budget':` → 4 spaces ข้างหน้า
- `if not is_admin():` → 8 spaces ข้างหน้า  
- `st.error(...)` → 12 spaces ข้างหน้า
- `return` → 12 spaces ข้างหน้า
- `from pages_budget...` → 8 spaces ข้างหน้า
- `render_budget()` → 8 spaces ข้างหน้า

**Tip:** Copy code ทั้ง block จากด้านบน → Paste ลงไปเลย — github.dev จะรักษา indent ให้

---

## 🔍 วิธีตรวจว่าทำถูก

หลัง save แล้ว:

1. ใน github.dev → กด `Cmd + F` 
2. พิมพ์: `'budget'`
3. ควรเจอ **2 ที่:**
   - `('budget', '💰 งบ'),`
   - `elif mode == 'budget':`

ถ้าเจอ 1 ที่ = แก้ไม่ครบ
ถ้าเจอ 0 ที่ = ลืม save

---

## 🚨 ถ้าผิดพลาด

### Error: `IndentationError`
→ Indent ผิด → ดูบรรทัดที่ error message บอก → เทียบกับบรรทัดเดิม

### Error: `ModuleNotFoundError: pages_budget`
→ ไม่มีไฟล์ `pages_budget.py` → กลับไปสร้างไฟล์นี้ก่อน

### App ไม่เห็นเมนู "💰 งบ"
→ ลืมแก้จุดที่ 1 (`admin_modes`)
