-- Neon SQL Editor-ல் இதை ஒருமுறை ரன் செய்யவும்
CREATE TABLE IF NOT EXISTS library_types (
  id   SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS libraries (
  id      SERIAL PRIMARY KEY,
  name    TEXT NOT NULL UNIQUE,
  type_id INT  NOT NULL REFERENCES library_types(id)
);
-- order_type: usage = பயன்பாட்டு அடிப்படையில் தள்ளுபடி ஆணை
--             unusable = பயன்படுத்த இயலாத நூல்கள் இருப்பு நீக்கம்
--             recovered = நூலகரிடம் வசூல் செய்யப்பட்ட நூல்கள் இருப்பு நீக்கம்
CREATE TABLE IF NOT EXISTS stock_verifications (
  id                  SERIAL PRIMARY KEY,
  order_type          TEXT NOT NULL CHECK (order_type IN ('usage','unusable','recovered')),
  file_no             TEXT NOT NULL,
  file_date           DATE NOT NULL,
  library_id          INT  NOT NULL REFERENCES libraries(id),
  library_type_id     INT  NOT NULL REFERENCES library_types(id),
  period_from         DATE,
  period_to           DATE,
  officer_report_date DATE,
  shortage_count      INT,
  shortage_value      NUMERIC(14,2),
  total_used_books    INT,
  stat_period_from    DATE,
  stat_period_to      DATE,
  created_at          TIMESTAMPTZ DEFAULT now()
);
-- பின்னர் தள்ளுபடி ஆணை PDF இணைக்க
CREATE TABLE IF NOT EXISTS verification_documents (
  id              SERIAL PRIMARY KEY,
  verification_id INT NOT NULL REFERENCES stock_verifications(id) ON DELETE CASCADE,
  doc_name        TEXT,
  doc_url         TEXT,
  uploaded_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sv_type ON stock_verifications(order_type);
CREATE INDEX IF NOT EXISTS idx_sv_lib  ON stock_verifications(library_id);

-- படி 1 (பழுதடைந்த நூல்கள் - ஒப்பப் புள்ளி கோர அனுமதி). Neon-ல் ரன் செய்யவும்
CREATE TABLE IF NOT EXISTS condemn_cases (
  id               SERIAL PRIMARY KEY,
  library_id       INT NOT NULL REFERENCES libraries(id),
  library_type_id  INT NOT NULL REFERENCES library_types(id),
  s1_file_no       TEXT NOT NULL,
  s1_file_date     DATE NOT NULL,
  s1_letter_date   DATE,
  s1_inspector_date DATE,
  s1_damaged_count INT,
  s1_damaged_value NUMERIC(14,2),
  created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cc_lib ON condemn_cases(library_id);
