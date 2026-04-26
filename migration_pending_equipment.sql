-- ============================================================
-- Migration: Pending Catalog Items
-- เมื่อ user สร้าง PO โดยใช้ "พิมพ์ชื่อเอง" ระบบจะสร้าง draft
-- equipment ในสถานะ pending รอ admin approve
-- ============================================================

-- เพิ่ม fields สำหรับ approval workflow
ALTER TABLE equipment
    ADD COLUMN IF NOT EXISTS approval_status TEXT DEFAULT 'approved',
    ADD COLUMN IF NOT EXISTS suggested_by UUID REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS suggested_by_name TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS suggested_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS suggested_from_po UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS suggested_notes TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS approved_by_name TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;

-- index หา pending เร็ว
CREATE INDEX IF NOT EXISTS idx_equipment_approval ON equipment(approval_status)
    WHERE approval_status = 'pending';

-- ทำให้ equipment ที่มีอยู่แล้วทั้งหมดเป็น 'approved' (default)
UPDATE equipment SET approval_status = 'approved' WHERE approval_status IS NULL;

SELECT
    'pending equipment fields added ✅' AS status,
    COUNT(*) FILTER (WHERE approval_status = 'approved') AS approved_count,
    COUNT(*) FILTER (WHERE approval_status = 'pending') AS pending_count
FROM equipment;
