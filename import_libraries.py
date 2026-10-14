"""பயன்பாடு: DATABASE_URL அமைத்த பின் -> python import_libraries.py libraries.csv
CSV: name,type (UTF-8). மீண்டும் ரன் செய்தாலும் நகல் உருவாகாது."""
import csv, os, sys, psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"]); cur = conn.cursor()
n = 0
with open(sys.argv[1], encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        name, typ = r["name"].strip(), r["type"].strip()
        if not name or not typ: continue
        cur.execute("INSERT INTO library_types(name) VALUES(%s) ON CONFLICT(name) DO NOTHING", (typ,))
        cur.execute("SELECT id FROM library_types WHERE name=%s", (typ,)); tid = cur.fetchone()[0]
        cur.execute("""INSERT INTO libraries(name,type_id) VALUES(%s,%s)
                       ON CONFLICT(name) DO UPDATE SET type_id=EXCLUDED.type_id""", (name, tid)); n += 1
conn.commit(); print(n, "நூலகங்கள் ஏற்றப்பட்டன")
