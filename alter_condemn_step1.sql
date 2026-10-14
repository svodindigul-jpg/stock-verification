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
