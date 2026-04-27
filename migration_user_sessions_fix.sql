-- ============================================================
-- Migration: user_sessions schema fix (C5)
--
-- แก้ปัญหา:
--   schema conflict ระหว่าง supabase_setup.sql กับ
--   migration_user_sessions.sql ที่ไม่ตรงกัน
--
-- หลังรันแล้ว user_sessions จะใช้ token เป็น primary key (ตามที่ code ใช้)
-- ============================================================

-- 1) ตรวจ schema ปัจจุบัน
DO $$
DECLARE
    col_count INT;
    has_id_column BOOLEAN;
BEGIN
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_name = 'user_sessions';
    
    IF col_count = 0 THEN
        RAISE NOTICE 'Table user_sessions does not exist — creating...';
        
        CREATE TABLE user_sessions (
            token TEXT PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_activity_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
        CREATE INDEX idx_user_sessions_activity ON user_sessions(last_activity_at);
        
        ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "user_sessions_all" ON user_sessions
            FOR ALL USING (true) WITH CHECK (true);
        
        RETURN;
    END IF;
    
    -- มี table แล้ว — ตรวจว่ามี column id ไหม
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_sessions'
          AND column_name = 'id'
    ) INTO has_id_column;
    
    IF has_id_column THEN
        RAISE NOTICE 'user_sessions has redundant id column — removing...';
        
        -- ตรวจว่า id เป็น PK ไหม → ถ้าใช่ ต้อง drop PK ก่อน
        IF EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = 'user_sessions'
              AND constraint_type = 'PRIMARY KEY'
              AND constraint_name LIKE '%pkey%'
        ) THEN
            ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS user_sessions_pkey;
        END IF;
        
        -- เปลี่ยน token เป็น PK ถ้ายังไม่ใช่
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = 'user_sessions'
              AND constraint_type = 'PRIMARY KEY'
        ) THEN
            ALTER TABLE user_sessions ADD PRIMARY KEY (token);
        END IF;
        
        -- ลบ id column
        ALTER TABLE user_sessions DROP COLUMN id;
        
        RAISE NOTICE 'Schema fixed: user_sessions now uses token as PK';
    ELSE
        RAISE NOTICE 'user_sessions schema is already correct';
    END IF;
END $$;


-- 2) Verification
SELECT 
    'user_sessions schema check' AS info,
    string_agg(column_name || '(' || data_type || ')', ', ' ORDER BY ordinal_position) AS columns
FROM information_schema.columns
WHERE table_name = 'user_sessions'
GROUP BY table_name;

-- ตรวจว่า PK เป็น token
SELECT 
    'primary key' AS info,
    string_agg(kcu.column_name, ', ') AS pk_columns
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_name = 'user_sessions'
  AND tc.constraint_type = 'PRIMARY KEY';

SELECT '✅ user_sessions schema fix complete' AS status;
