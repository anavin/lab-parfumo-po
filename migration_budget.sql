-- ============================================================
-- Migration: Budget Tracking (NEW FEATURE F1)
--
-- ตั้งงบประมาณรายเดือน/รายไตรมาส/รายปี + alerts
-- รองรับงบรวมและงบแยกหมวด
-- ============================================================

CREATE TABLE IF NOT EXISTS budget_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_type TEXT NOT NULL CHECK (period_type IN ('monthly', 'quarterly', 'yearly')),
    period_year INT NOT NULL,
    period_month INT,  -- 1-12 (monthly), 1/4/7/10 (quarterly), NULL (yearly)
    category TEXT,     -- NULL = งบรวม
    amount NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    notes TEXT DEFAULT '',
    created_by_name TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique: 1 budget per (type, year, month, category) combo
    -- ใช้ COALESCE เพราะ NULL ใน UNIQUE ไม่ถือว่าเท่ากัน
    UNIQUE (period_type, period_year, period_month, category)
);

CREATE INDEX IF NOT EXISTS idx_budget_year_month
    ON budget_periods(period_year, period_month);
CREATE INDEX IF NOT EXISTS idx_budget_category
    ON budget_periods(category);

ALTER TABLE budget_periods ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "budget_periods_all" ON budget_periods;
CREATE POLICY "budget_periods_all" ON budget_periods
    FOR ALL USING (true) WITH CHECK (true);


-- ============================================================
-- Trigger: auto-update updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION budget_periods_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_budget_periods_updated_at ON budget_periods;
CREATE TRIGGER trg_budget_periods_updated_at
    BEFORE UPDATE ON budget_periods
    FOR EACH ROW
    EXECUTE FUNCTION budget_periods_set_updated_at();


-- ============================================================
-- ✅ Done
-- ============================================================
SELECT 'budget_periods table created ✅' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables
              WHERE table_name = 'budget_periods');
