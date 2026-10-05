-- Erinnerungen (2026-10-05). Run once:
--   npx wrangler d1 execute fwmc-training-codes --remote --file=migrations/0001_reminders.sql
-- (The Worker also creates these on first use, IF NOT EXISTS.)
CREATE TABLE IF NOT EXISTS push_subs (
  id TEXT PRIMARY KEY,            -- sha256 of the endpoint
  endpoint TEXT NOT NULL,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS push_reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sub_id TEXT NOT NULL,
  at TEXT NOT NULL,               -- ISO UTC
  title TEXT NOT NULL,
  body TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS push_reminders_at ON push_reminders (at);
CREATE INDEX IF NOT EXISTS push_reminders_sub ON push_reminders (sub_id);
