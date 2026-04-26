-- ============================================================
-- Migration: เพิ่มหลายรูปให้ Equipment Catalog
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูลเดิม
-- ============================================================

-- 1) เพิ่ม column image_urls (รองรับหลายรูป)
ALTER TABLE equipment
    ADD COLUMN IF NOT EXISTS image_urls JSONB DEFAULT '[]';

-- 2) Migrate รูปเดิมเข้า array (ถ้ามี image_url แต่ image_urls ว่าง)
UPDATE equipment
SET image_urls = jsonb_build_array(image_url)
WHERE image_url IS NOT NULL
  AND image_url != ''
  AND (image_urls IS NULL OR image_urls = '[]'::jsonb);

-- 3) ตรวจผล
SELECT
    'Equipment migration completed ✅' AS status,
    COUNT(*) AS total_items,
    COUNT(*) FILTER (WHERE jsonb_array_length(image_urls) > 0) AS items_with_images
FROM equipment;
