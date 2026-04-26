-- ============================================================
-- Migration: Session Persistence (Login ค้างหลัง Refresh)
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูลเดิม
-- ============================================================

-- 1) สร้างตาราง user_sessions เก็บ session tokens
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2) Index สำหรับค้นหา token เร็ว
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity_at);

-- 3) RLS — เปิดให้ใช้งานได้
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "user_sessions_all" ON user_sessions;
CREATE POLICY "user_sessions_all" ON user_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- 4) ตรวจผล
SELECT 'user_sessions table created ✅' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions');

SELECT
    COUNT(*) AS active_sessions
FROM user_sessions
WHERE last_activity_at > NOW() - INTERVAL '5 minutes';
