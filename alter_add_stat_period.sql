ALTER TABLE stock_verifications
  ADD COLUMN IF NOT EXISTS stat_period_from DATE,
  ADD COLUMN IF NOT EXISTS stat_period_to   DATE;
