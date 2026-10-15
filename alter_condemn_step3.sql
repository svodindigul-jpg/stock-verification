-- படி 1-ல் கிளைப் பதிவெண் (முதல் - முடிய) + படி 3 (இருப்பு நீக்க அனுமதி ஆணை). Neon SQL Editor-ல் ஒருமுறை ரன் செய்யவும்
ALTER TABLE condemn_cases
  ADD COLUMN IF NOT EXISTS s1_acc_from BIGINT,
  ADD COLUMN IF NOT EXISTS s1_acc_to   BIGINT,
  ADD COLUMN IF NOT EXISTS s3_file_date         DATE,
  ADD COLUMN IF NOT EXISTS s3_letter_date       DATE,
  ADD COLUMN IF NOT EXISTS s3_half_count        INT,
  ADD COLUMN IF NOT EXISTS s3_half_amount       NUMERIC(14,2),
  ADD COLUMN IF NOT EXISTS s3_half_paid_date    DATE,
  ADD COLUMN IF NOT EXISTS s3_auction_paid_date DATE;
