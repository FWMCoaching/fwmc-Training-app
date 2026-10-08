-- Trainer-Dashboard storage (kp20, 2026-10-08): Bausätze, client plans
-- (Kürzel only, never names), saved Stände and the selected client, so the
-- dashboard is the same on every device. Admin-only (/admin/items).
-- Apply with:  npx wrangler d1 migrations apply fwmc-training-codes --remote
-- (The Worker also creates this table on first use, IF NOT EXISTS.)
CREATE TABLE IF NOT EXISTS trainer_items (
  kind TEXT NOT NULL,             -- bausaetze | plans | plan-versions | current
  id TEXT NOT NULL,               -- Bausatz id, Kürzel, or "current"
  data TEXT NOT NULL,             -- JSON
  updated_at INTEGER NOT NULL,    -- ms, the dashboard's clock
  PRIMARY KEY (kind, id)
);
