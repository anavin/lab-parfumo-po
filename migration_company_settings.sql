-- ============================================================
-- Migration: Company Settings
-- เก็บข้อมูลบริษัทใน DB เพื่อให้ admin แก้ผ่าน UI ได้
-- ============================================================

CREATE TABLE IF NOT EXISTS company_settings (
    id INT PRIMARY KEY DEFAULT 1,
    name TEXT DEFAULT 'Lab Parfumo',
    name_th TEXT DEFAULT 'แล็บ พาฟูโม่',
    address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    tax_id TEXT DEFAULT '',
    website TEXT DEFAULT '',
    logo_url TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by_name TEXT DEFAULT '',
    CONSTRAINT singleton CHECK (id = 1)
);

-- ใส่แถวเริ่มต้น (มีแถวเดียวเท่านั้น)
INSERT INTO company_settings (id, name, name_th, address, phone, email, tax_id, website)
VALUES (
    1,
    'Lab Parfumo',
    'บริษัท ทัช ไดเวอร์เจนซ์ จำกัด',
    '',
    '',
    '',
    '0115564002651',
    'www.labparfumo.com'
)
ON CONFLICT (id) DO NOTHING;

ALTER TABLE company_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "company_settings_all" ON company_settings;
CREATE POLICY "company_settings_all" ON company_settings
    FOR ALL USING (true) WITH CHECK (true);

SELECT 'company_settings table ready ✅' AS status;
