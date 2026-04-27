# 📦 Patches Pack — Lab Parfumo PO Pro

ชุด patch files พร้อมใช้ — แก้ทุก **Critical** และ **High** issues ที่ระบุใน `CODE_REVIEW.md`  
รวมถึงเพิ่ม **2 Features** ใหม่: 💰 Budget Tracking + 📊 Period PDF Reports

---

## 🗂️ เนื้อหาในแพ็ค

### 🐍 Python Files (วาง replace ของเดิม)

| ไฟล์ | คำอธิบาย | บรรทัดเปลี่ยนหลัก |
|---|---|---|
| `helpers.py` | + `esc()` HTML escape, Status constants, timezone helpers, config | NEW (ขยายจากเดิม) |
| `database.py` | bcrypt password, atomic counters, soft delete, type hints | ~50% rewrite |
| `pdf_generator.py` | HTML escape ทุกที่ + `generate_period_report_pdf()` | + 200 บรรทัด |
| `pages_budget.py` | **NEW** — Budget UI + period PDF generation | NEW |
| `requirements.txt` | + `bcrypt>=4.0.0` | +1 บรรทัด |

### 🗄️ SQL Migrations (รันใน Supabase ตามลำดับ)

| ไฟล์ | คำอธิบาย |
|---|---|
| `migration_user_sessions_fix.sql` | แก้ schema conflict (C5) |
| `migration_atomic_counter.sql` | แก้ race conditions (C3, C4) |
| `migration_security_v2.sql` | bcrypt support + soft-delete columns (S1, B1, B2) |
| `migration_budget.sql` | งบประมาณ (Feature F1) |

### 📚 Documentation

| ไฟล์ | คำอธิบาย |
|---|---|
| `DEPLOY.md` | คู่มือ deploy ใหม่ — รวมทุก migration ตามลำดับ + troubleshoot |
| `CODE_REVIEW.md` | รายงานการ review เต็มฉบับ |

### 🧪 Tests

| ไฟล์ | คำอธิบาย |
|---|---|
| `tests/test_database.py` | Unit tests สำหรับ password, escape, validation |

---

## 🚀 ลำดับการ Apply Patches

### Step 1 — Backup ก่อน!
```bash
cp -r /path/to/lab-parfumo-po-pro /path/to/lab-parfumo-po-pro.backup-$(date +%Y%m%d)
```

### Step 2 — Update Python files
แทนที่ไฟล์เดิม:
```
patches/helpers.py        → ./helpers.py
patches/database.py       → ./database.py
patches/pdf_generator.py  → ./pdf_generator.py
patches/requirements.txt  → ./requirements.txt
```

เพิ่มไฟล์ใหม่:
```
patches/pages_budget.py   → ./pages_budget.py (ใหม่!)
patches/tests/            → ./tests/ (ใหม่!)
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
# จะติดตั้ง bcrypt เพิ่มอัตโนมัติ
```

### Step 4 — Run SQL migrations ตามลำดับ
ใน Supabase SQL Editor:
1. `migration_user_sessions_fix.sql` (เริ่มจากนี้ก่อน)
2. `migration_atomic_counter.sql`
3. `migration_security_v2.sql`
4. `migration_budget.sql`

ตรวจ output ว่าไม่มี error

### Step 5 — Update `app.py` เพิ่ม navigation สำหรับ Budget feature

หาในไฟล์ `app.py` ส่วน `admin_modes`:
```python
admin_modes = [
    ('equipment', '📦 Catalog'),
    ('reports', '📈 รายงาน'),
    ('users', '👥 ผู้ใช้'),
    ('settings', '⚙️ ตั้งค่า'),
]
```

เพิ่ม:
```python
admin_modes = [
    ('equipment', '📦 Catalog'),
    ('budget', '💰 งบ'),       # ⭐ NEW
    ('reports', '📈 รายงาน'),
    ('users', '👥 ผู้ใช้'),
    ('settings', '⚙️ ตั้งค่า'),
]
```

หาในส่วน `main()` ที่ route mode:
```python
elif mode == 'reports':
    if not is_admin():
        st.error("❌ เฉพาะแอดมิน")
        return
    render_reports()
```

เพิ่มก่อนหน้า:
```python
elif mode == 'budget':
    if not is_admin():
        st.error("❌ เฉพาะแอดมิน")
        return
    from pages_budget import render_budget
    render_budget()
```

### Step 6 — ทดสอบ
```bash
# Run tests
python -m pytest tests/test_database.py -v

# Start app
streamlit run app.py
```

ตรวจ:
- [ ] Login ปกติ — user เก่าใช้ SHA-256 → ระบบ auto-upgrade เป็น bcrypt ตอน login
- [ ] สร้าง PO + ดู PDF — ภาษาไทยแสดงถูก, ไม่มี HTML แตก
- [ ] Withdraw stock — ลองเบิกพร้อมกันหลายๆ ครั้งเร็วๆ → stock ไม่ติดลบ
- [ ] เข้าหน้า "💰 งบ" → ตั้งงบใหม่ + ดู dashboard
- [ ] Generate period report PDF

---

## ⚠️ สิ่งที่ต้องระวัง

### Backward compatibility
- ✅ User เก่าที่ใช้ SHA-256 ยัง login ได้ — ระบบ auto-upgrade hash
- ✅ ไม่ต้อง force user เปลี่ยนรหัส
- ✅ Schema เปลี่ยนแบบ ADD COLUMN IF NOT EXISTS — ไม่ลบข้อมูล
- ⚠️ User ที่ถูก soft-delete จะมี username เป็น `_del_xxx_yyyy` — ถ้าจะ restore ให้ admin update username ก่อน

### Migration safety
- 🟢 `migration_atomic_counter.sql` — ปลอดภัยใช้กับ DB ที่มีข้อมูลแล้ว
- 🟢 `migration_security_v2.sql` — แค่ ADD COLUMN ปลอดภัย
- 🟡 `migration_user_sessions_fix.sql` — DROP COLUMN id ถ้ามี → session ทุกอันใช้ได้เหมือนเดิม
- 🟢 `migration_budget.sql` — สร้าง table ใหม่ ไม่กระทบของเดิม

### Performance
- bcrypt ช้ากว่า SHA-256 ~100x (~ 250ms ต่อ login) — ไม่เป็นปัญหาเพราะ login ไม่บ่อย
- atomic counter via Postgres function = เร็วกว่าเดิมจริง (1 round-trip แทน 2)

---

## 🔬 What's NOT changed

ผม **ไม่ได้** แก้ไฟล์ต่อไปนี้ เพราะ:
- `app.py` — ใหญ่มาก (1700+ บรรทัด) ส่วนใหญ่เป็น render code ที่ปลอดภัย — แค่ต้องใส่ navigation เพิ่ม (Step 5)
- `pages_po.py`, `pages_admin.py`, `pages_withdraw.py` — มีจุด `unsafe_allow_html=True` หลายแห่ง แต่ส่วนใหญ่ user input ตรงไปตรงมา
- `notify.py`, `supabase_setup.sql`, etc.

หากต้องการแก้ทุกไฟล์ — ผมแนะนำให้ทำ **Sprint 2** หลังจาก deploy critical fixes ก่อน

---

## 🐛 Known Limitations

1. **app.py** ยังมี `unsafe_allow_html=True` กับ user input อยู่บ้าง — ในแพ็คนี้แก้แค่ pdf_generator (ที่อันตรายสุด) ส่วน UI ยังเสี่ยง XSS เล็กน้อย แต่ requires admin to set malicious user names — risk ต่ำ
2. **RLS policies** ทั้งหมดยัง `USING (true)` — ต้อง refactor ใหญ่ภายหลัง (S3 ใน CODE_REVIEW.md)
3. **Welcome email plain password** — ยังไม่แก้ในแพ็คนี้ — คำแนะนำใน CODE_REVIEW.md (S4)

---

## 📞 หากมีปัญหา

1. Check `CODE_REVIEW.md` — มีรายละเอียดแต่ละ issue + fix
2. Check `DEPLOY.md` — มี troubleshooting section
3. Run `python -m pytest tests/test_database.py -v` — ดูว่า logic ใหม่ทำงานถูกต้อง

---

**Patches generated:** 2026-04-27  
**Reviewed code commit:** uploaded snapshot
