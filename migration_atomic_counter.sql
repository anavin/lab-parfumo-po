-- ============================================================
-- Migration: Atomic Counter Functions (Race Condition Fix)
-- 
-- แก้ปัญหา:
--   C3 — generate_po_number race condition (PO numbers ซ้ำกัน)
--   C4 — withdraw_stock race condition (stock ติดลบ)
--
-- รันใน Supabase SQL Editor ครั้งเดียว — ปลอดภัย ไม่ลบข้อมูล
-- ============================================================

-- ============================================================
-- 1) Atomic PO number generation
-- ============================================================
CREATE OR REPLACE FUNCTION next_po_number(year_int INT)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    counter_id TEXT := 'po_' || year_int::TEXT;
    new_value INT;
BEGIN
    -- UPSERT: insert ถ้ายังไม่มี / +1 ถ้ามี — atomic
    INSERT INTO counters (id, value)
    VALUES (counter_id, 1)
    ON CONFLICT (id) DO UPDATE
        SET value = counters.value + 1
    RETURNING value INTO new_value;
    
    RETURN 'PO-' || year_int::TEXT || '-' || LPAD(new_value::TEXT, 4, '0');
END;
$$;

COMMENT ON FUNCTION next_po_number(INT) IS
    'Atomically increment counter and return formatted PO number. Race-condition free.';


-- ============================================================
-- 2) Atomic stock withdrawal
--
-- Returns JSONB:
--   { success: true, new_stock: int, name: text, unit: text }
--   { success: false, error: 'insufficient_stock', current_stock: int }
--   { success: false, error: 'not_found' }
-- ============================================================
CREATE OR REPLACE FUNCTION withdraw_stock(
    p_equipment_id UUID,
    p_qty NUMERIC
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    eq_row RECORD;
    new_stock INT;
BEGIN
    -- SELECT FOR UPDATE: ล็อค row ในระหว่างที่กำลัง update
    SELECT id, name, unit, stock INTO eq_row
    FROM equipment
    WHERE id = p_equipment_id
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'not_found');
    END IF;
    
    IF eq_row.stock < p_qty THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'insufficient_stock',
            'current_stock', eq_row.stock,
            'name', eq_row.name,
            'unit', eq_row.unit
        );
    END IF;
    
    -- หัก stock — atomic เพราะ row ถูก lock
    UPDATE equipment
    SET stock = stock - p_qty::INT
    WHERE id = p_equipment_id
    RETURNING stock INTO new_stock;
    
    RETURN jsonb_build_object(
        'success', true,
        'new_stock', new_stock,
        'name', eq_row.name,
        'unit', eq_row.unit
    );
END;
$$;

COMMENT ON FUNCTION withdraw_stock(UUID, NUMERIC) IS
    'Atomically check and decrement stock. Race-condition free via SELECT FOR UPDATE.';


-- ============================================================
-- 3) Test แบบ smoke
-- ============================================================
SELECT 'Atomic functions installed ✅' AS status;

-- ตรวจว่า function สร้างสำเร็จ
SELECT proname AS function_name, pronargs AS num_args
FROM pg_proc
WHERE proname IN ('next_po_number', 'withdraw_stock');
