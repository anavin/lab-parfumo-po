-- ============================================================
-- Migration: Security V2 — bcrypt support + soft delete fields
--
-- แก้ปัญหา:
--   S1 — bcrypt password hashing (auto-migrate from SHA-256)
--   B1 — Soft delete user (รักษาประวัติ)
--   B2 — Soft reject equipment (รักษาประวัติ)
--
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูล
-- 
-- หลังรันแล้ว Code (database.py) จะ auto-migrate password hash
-- ตอน user คนนั้น login ครั้งต่อไป — ไม่ต้อง force ทุกคนพร้อมกัน
-- ============================================================

-- ============================================================
-- 1) Password hash column ขยายเป็น bcrypt-friendly (60 chars)
-- ============================================================
-- bcrypt = 60 chars, SHA-256 hex = 64 chars → TEXT รองรับทั้งคู่อยู่แล้ว
-- ไม่ต้องแก้ schema — แค่ verify ว่า column TYPE = TEXT
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name = 'password_hash'
          AND data_type != 'text'
    ) THEN
        RAISE NOTICE 'WARNING: password_hash column is not TEXT — please verify';
    END IF;
END $$;


-- ============================================================
-- 2) Equipment — soft reject fields
-- ============================================================
ALTER TABLE equipment
    ADD COLUMN IF NOT EXISTS rejected_reason TEXT,
    ADD COLUMN IF NOT EXISTS rejected_by_name TEXT,
    ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_equipment_rejected
    ON equipment(approval_status)
    WHERE approval_status = 'rejected';


-- ============================================================
-- 3) FK — เปลี่ยน purchase_orders.created_by → ON DELETE SET NULL
--    (กรณีที่จะ hard delete user ในอนาคต)
-- ============================================================
DO $$
BEGIN
    -- drop old FK ถ้ามี
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'purchase_orders'
          AND constraint_name = 'purchase_orders_created_by_fkey'
    ) THEN
        ALTER TABLE purchase_orders
            DROP CONSTRAINT purchase_orders_created_by_fkey;
    END IF;
    
    -- add ใหม่
    ALTER TABLE purchase_orders
        ADD CONSTRAINT purchase_orders_created_by_fkey
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
END $$;


-- ============================================================
-- 4) Verification
-- ============================================================
SELECT 'Security V2 migration ✅' AS status;

SELECT 
    'equipment soft-reject columns' AS item,
    COUNT(*) AS columns_added
FROM information_schema.columns
WHERE table_name = 'equipment'
  AND column_name IN ('rejected_reason', 'rejected_by_name', 'rejected_at');

-- ตรวจ password hash format
SELECT
    'password format breakdown' AS info,
    SUM(CASE WHEN password_hash LIKE '$2%' THEN 1 ELSE 0 END) AS bcrypt_users,
    SUM(CASE WHEN password_hash NOT LIKE '$2%' AND length(password_hash) = 64 THEN 1 ELSE 0 END) AS legacy_sha256_users,
    SUM(CASE WHEN password_hash IS NULL OR password_hash = '' THEN 1 ELSE 0 END) AS no_password_users
FROM users;
