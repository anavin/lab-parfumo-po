-- ============================================================
-- Migration: Production Hardening
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูลเดิม
-- ============================================================

-- 1) เพิ่ม columns ในตาราง users สำหรับ security
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS failed_login_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;

-- 2) สร้างตาราง login_attempts สำหรับ track ความพยายาม login
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, created_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(created_at);

-- 3) RLS — เปิด policy ให้ insert/select ได้
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "login_attempts_all" ON login_attempts;
CREATE POLICY "login_attempts_all" ON login_attempts
    FOR ALL USING (true) WITH CHECK (true);

-- 4) auto-cleanup old login_attempts (เก็บแค่ 30 วัน) - optional
-- DELETE FROM login_attempts WHERE created_at < NOW() - INTERVAL '30 days';

-- ============================================================
-- ตรวจผล
-- ============================================================
SELECT
    'users columns added' AS status,
    column_name
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name IN ('last_login_at', 'failed_login_count', 'must_change_password', 'password_changed_at');

SELECT 'login_attempts table created ✅' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'login_attempts');
