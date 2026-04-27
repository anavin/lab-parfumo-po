-- ============================================================
-- Lab Parfumo PO System (Pro) - Supabase Setup
-- 2 Roles: requester (ผู้สั่ง, ไม่เห็นราคา/supplier) / admin (เห็นทุกอย่าง)
-- ============================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'requester',  -- 'requester' หรือ 'admin'
    email TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories
CREATE TABLE IF NOT EXISTS equipment_categories (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku TEXT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT DEFAULT 'ชิ้น',
    description TEXT DEFAULT '',
    last_cost NUMERIC(10, 2) DEFAULT 0,
    stock INTEGER DEFAULT 0,
    image_url TEXT,
    image_urls JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number TEXT UNIQUE NOT NULL,
    
    -- Items
    items JSONB NOT NULL DEFAULT '[]',
    
    -- ข้อมูลที่ผู้สั่งกรอก
    purpose TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    
    -- ข้อมูลที่จัดซื้อกรอก (เห็นเฉพาะ admin)
    supplier_name TEXT,
    supplier_contact TEXT DEFAULT '',
    subtotal NUMERIC(12, 2) DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    shipping_fee NUMERIC(12, 2) DEFAULT 0,
    vat NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) DEFAULT 0,
    procurement_notes TEXT DEFAULT '',
    
    -- Tracking
    tracking_number TEXT,
    attachment_urls JSONB DEFAULT '[]',
    
    -- Status & dates
    status TEXT NOT NULL DEFAULT 'รอจัดซื้อดำเนินการ',
    ordered_date DATE,
    expected_date DATE,
    received_date DATE,
    
    -- Created by
    created_by UUID REFERENCES users(id),
    created_by_name TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Deliveries (รับของ - 1 PO อาจมีหลายครั้งถ้าทยอยส่ง)
CREATE TABLE IF NOT EXISTS po_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    delivery_no INTEGER DEFAULT 1,
    received_date DATE,
    received_by_name TEXT,
    items_received JSONB DEFAULT '[]',  -- [{equipment_id, name, qty_ordered, qty_received, qty_damaged, notes}]
    overall_condition TEXT DEFAULT 'ปกติ',  -- 'ปกติ', 'มีของเสียหาย', 'ขาดจำนวน', 'ส่งผิด', 'อื่นๆ'
    issue_description TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    image_urls JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Activity log
CREATE TABLE IF NOT EXISTS po_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    user_name TEXT,
    user_role TEXT,
    action TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments
CREATE TABLE IF NOT EXISTS po_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    user_name TEXT,
    user_role TEXT,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notifications (ในแอป)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    po_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT DEFAULT '',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Counters
CREATE TABLE IF NOT EXISTS counters (
    id TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment(category);
CREATE INDEX IF NOT EXISTS idx_po_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_created_by ON purchase_orders(created_by);
CREATE INDEX IF NOT EXISTS idx_po_created_at ON purchase_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_po_expected ON purchase_orders(expected_date);
CREATE INDEX IF NOT EXISTS idx_deliveries_po ON po_deliveries(po_id);
CREATE INDEX IF NOT EXISTS idx_activities_po ON po_activities(po_id);
CREATE INDEX IF NOT EXISTS idx_comments_po ON po_comments(po_id);
CREATE INDEX IF NOT EXISTS idx_notif_user ON notifications(user_id);

-- RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipment_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE po_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE po_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE po_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE counters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "all_users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_equipment" ON equipment FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_equipment_categories" ON equipment_categories FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_purchase_orders" ON purchase_orders FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_po_deliveries" ON po_deliveries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_po_activities" ON po_activities FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_po_comments" ON po_comments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_notifications" ON notifications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "all_counters" ON counters FOR ALL USING (true) WITH CHECK (true);

-- Seed categories
INSERT INTO equipment_categories (name) VALUES
    ('ขวดบรรจุ'), ('ฝา/จุก'), ('กล่องบรรจุภัณฑ์'),
    ('สติกเกอร์/ฉลาก'), ('อุปกรณ์อื่นๆ')
ON CONFLICT (name) DO NOTHING;

-- Default admin user
-- username: admin, password: admin123
-- (sha256 hash ของ "admin123")
INSERT INTO users (username, password_hash, full_name, role) VALUES
    ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'ผู้ดูแลระบบ', 'admin')
ON CONFLICT (username) DO NOTHING;

-- ============================================================
-- Security columns + login_attempts table (Production hardening)
-- ============================================================
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS failed_login_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_user ON login_attempts(username, created_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_time ON login_attempts(created_at);

ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "login_attempts_all" ON login_attempts;
CREATE POLICY "login_attempts_all" ON login_attempts
    FOR ALL USING (true) WITH CHECK (true);

-- User sessions (จำตอน refresh)
CREATE TABLE IF NOT EXISTS user_sessions (
    token TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity_at);

ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "user_sessions_all" ON user_sessions;
CREATE POLICY "user_sessions_all" ON user_sessions
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- เสร็จ! ต่อไปสร้าง 3 Storage Buckets:
-- 1. "equipment-images" (Public)
-- 2. "delivery-images" (Public)
-- 3. "po-attachments" (Public)
-- พร้อม policies อนุญาต SELECT/INSERT/DELETE สำหรับ anon
-- ============================================================
