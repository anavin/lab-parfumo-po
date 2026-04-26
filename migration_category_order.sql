-- ============================================================
-- Migration: เพิ่ม display_order ให้ Categories จัดเรียงได้
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูลเดิม
-- ============================================================

-- 1) เพิ่ม column display_order
ALTER TABLE equipment_categories
    ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- 2) Initialize ลำดับตาม created_at (ของเก่าได้ลำดับตามที่สร้าง)
WITH ordered AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn
    FROM equipment_categories
)
UPDATE equipment_categories
SET display_order = ordered.rn
FROM ordered
WHERE equipment_categories.id = ordered.id
  AND (equipment_categories.display_order IS NULL OR equipment_categories.display_order = 0);

-- 3) Index สำหรับเรียงเร็ว
CREATE INDEX IF NOT EXISTS idx_categories_order
    ON equipment_categories(display_order);

-- 4) ตรวจผล
SELECT
    'Categories order migration completed ✅' AS status,
    COUNT(*) AS total_categories,
    MIN(display_order) AS min_order,
    MAX(display_order) AS max_order
FROM equipment_categories;

SELECT name, display_order
FROM equipment_categories
ORDER BY display_order;
