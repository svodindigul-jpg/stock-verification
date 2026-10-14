import os
import psycopg2, psycopg2.extras
from flask import Flask, render_template, request, redirect, url_for, flash, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me")

KINDS = {
    "usage":     {"title": "பயன்பாட்டு அடிப்படையில் தள்ளுபடி ஆணை", "full": True},
    "unusable":  {"title": "பயன்படுத்த இயலாத நூல்கள் இருப்பு நீக்கம்", "full": False},
    "recovered": {"title": "நூலகரிடம் வசூல் செய்யப்பட்ட நூல்கள் இருப்பு நீக்கம்", "full": False},
}

def run(sql, args=(), fetch="all"):
    conn = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, args)
            if fetch == "all": return cur.fetchall()
            if fetch == "one": return cur.fetchone()
    finally:
        conn.close()

@app.template_filter("dmy")
def dmy(d): return d.strftime("%d-%m-%Y") if d else "—"

def kind_or_404(kind):
    if kind not in KINDS: abort(404)
    return KINDS[kind]

def val(name, cast=str):
    v = (request.form.get(name) or "").strip()
    if not v: return None
    return cast(v)

@app.route("/")
def index():
    counts = {r["order_type"]: r["c"] for r in run(
        "SELECT order_type, COUNT(*) c FROM stock_verifications GROUP BY order_type")}
    return render_template("index.html", kinds=KINDS, counts=counts)

@app.route("/<kind>/")
def listing(kind):
    meta = kind_or_404(kind)
    rows = run("""SELECT s.*, l.name lib_name, t.name type_name
                  FROM stock_verifications s
                  JOIN libraries l ON l.id=s.library_id
                  JOIN library_types t ON t.id=s.library_type_id
                  WHERE s.order_type=%s ORDER BY s.file_date DESC, s.id DESC""", (kind,))
    return render_template("list.html", kind=kind, meta=meta, rows=rows)

@app.route("/<kind>/new", methods=["GET", "POST"])
@app.route("/<kind>/<int:rid>/edit", methods=["GET", "POST"])
def form(kind, rid=None):
    meta = kind_or_404(kind)
    row = run("SELECT * FROM stock_verifications WHERE id=%s AND order_type=%s", (rid, kind), "one") if rid else None
    if rid and not row: abort(404)
    if request.method == "POST":
        full = meta["full"]
        data = [val("file_no"), val("file_date"), val("library_id", int), val("library_type_id", int),
                val("period_from") if full else None, val("period_to") if full else None,
                val("officer_report_date") if full else None,
                val("shortage_count", int) if full else None,
                val("shortage_value") if full else None,
                val("total_used_books", int) if full else None]
        if not (data[0] and data[1] and data[2] and data[3]):
            flash("கோப்பு ந.க.எண்., நாள், நூலகம், நூலக வகை ஆகியவை கட்டாயம்.", "err")
        else:
            if rid:
                run("""UPDATE stock_verifications SET file_no=%s,file_date=%s,library_id=%s,library_type_id=%s,
                       period_from=%s,period_to=%s,officer_report_date=%s,shortage_count=%s,shortage_value=%s,
                       total_used_books=%s WHERE id=%s""", data + [rid], None)
            else:
                run("""INSERT INTO stock_verifications(file_no,file_date,library_id,library_type_id,period_from,
                       period_to,officer_report_date,shortage_count,shortage_value,total_used_books,order_type)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", data + [kind], None)
            flash("பதிவு சேமிக்கப்பட்டது.", "ok")
            return redirect(url_for("listing", kind=kind))
    libs = run("""SELECT l.id, l.name, l.type_id FROM libraries l ORDER BY l.name""")
    types = run("SELECT id, name FROM library_types ORDER BY name")
    return render_template("form.html", kind=kind, meta=meta, row=row or {}, libs=libs, types=types)

@app.post("/<kind>/<int:rid>/delete")
def delete(kind, rid):
    kind_or_404(kind)
    run("DELETE FROM stock_verifications WHERE id=%s AND order_type=%s", (rid, kind), None)
    flash("பதிவு நீக்கப்பட்டது.", "ok")
    return redirect(url_for("listing", kind=kind))

if __name__ == "__main__":
    app.run(debug=True)
