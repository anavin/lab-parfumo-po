-- ============================================================
-- Migration: Auto-save Draft PO
-- รันใน Supabase SQL Editor ครั้งเดียว
-- ============================================================

CREATE TABLE IF NOT EXISTS po_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    items JSONB NOT NULL DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)  -- 1 draft ต่อ user
);

CREATE INDEX IF NOT EXISTS idx_po_drafts_user ON po_drafts(user_id);

ALTER TABLE po_drafts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "po_drafts_all" ON po_drafts;
CREATE POLICY "po_drafts_all" ON po_drafts
    FOR ALL USING (true) WITH CHECK (true);

SELECT 'po_drafts table created ✅' AS status
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'po_drafts');
