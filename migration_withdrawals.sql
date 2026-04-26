-- ============================================================
-- Migration: Stock Withdrawal — เบิกสินค้าไปใช้
-- รันใน Supabase SQL Editor ครั้งเดียว
-- ============================================================

CREATE TABLE IF NOT EXISTS withdrawals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    equipment_name TEXT NOT NULL,
    qty NUMERIC NOT NULL,
    unit TEXT DEFAULT 'ชิ้น',
    purpose TEXT DEFAULT '',
    withdrawn_by UUID REFERENCES users(id),
    withdrawn_by_name TEXT DEFAULT '',
    withdrawn_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_withdrawals_equipment ON withdrawals(equipment_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_user ON withdrawals(withdrawn_by);
CREATE INDEX IF NOT EXISTS idx_withdrawals_date ON withdrawals(withdrawn_at DESC);

ALTER TABLE withdrawals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "withdrawals_all" ON withdrawals;
CREATE POLICY "withdrawals_all" ON withdrawals
    FOR ALL USING (true) WITH CHECK (true);

SELECT 'withdrawals table created ✅' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'withdrawals');
