import os, io
import psycopg2, psycopg2.extras
from flask import Flask, send_file, render_template, request, redirect, url_for, flash, abort

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

def fname(lib_name, suffix):
    import re
    from order_pdf import clean_name
    name = re.sub(r'[\\/:*?"<>|]', "", clean_name(lib_name)).strip()
    return f"{name}-{suffix}.pdf"

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
    counts["unusable"] = run("SELECT COUNT(*) c FROM condemn_cases", (), "one")["c"]
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
                val("total_used_books", int) if full else None,
                val("stat_period_from") if full else None, val("stat_period_to") if full else None]
        if not (data[0] and data[1] and data[2] and data[3]):
            flash("கோப்பு ந.க.எண்., நாள், நூலகம், நூலக வகை ஆகியவை கட்டாயம்.", "err")
        else:
            if rid:
                run("""UPDATE stock_verifications SET file_no=%s,file_date=%s,library_id=%s,library_type_id=%s,
                       period_from=%s,period_to=%s,officer_report_date=%s,shortage_count=%s,shortage_value=%s,
                       total_used_books=%s,stat_period_from=%s,stat_period_to=%s WHERE id=%s""", data + [rid], None)
            else:
                run("""INSERT INTO stock_verifications(file_no,file_date,library_id,library_type_id,period_from,
                       period_to,officer_report_date,shortage_count,shortage_value,total_used_books,stat_period_from,stat_period_to,order_type)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", data + [kind], None)
            flash("பதிவு சேமிக்கப்பட்டது.", "ok")
            return redirect(url_for("listing", kind=kind))
    libs = run("""SELECT l.id, l.name, l.type_id FROM libraries l ORDER BY l.name""")
    types = run("SELECT id, name FROM library_types ORDER BY id")
    return render_template("form.html", kind=kind, meta=meta, row=row or {}, libs=libs, types=types)

@app.route("/usage/<int:rid>/pdf")
def order_pdf(rid):
    from order_pdf import build_order
    r = run("""SELECT s.*, l.name lib_name, t.name type_name FROM stock_verifications s
               JOIN libraries l ON l.id=s.library_id JOIN library_types t ON t.id=s.library_type_id
               WHERE s.id=%s AND s.order_type='usage'""", (rid,), "one")
    if not r: abort(404)
    try:
        data = build_order(r)
    except AssertionError:
        flash("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை.", "err"); return redirect(url_for("listing", kind="usage"))
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True,
                     download_name=fname(r["lib_name"], "usage removal"))

@app.post("/<kind>/<int:rid>/delete")
def delete(kind, rid):
    kind_or_404(kind)
    run("DELETE FROM stock_verifications WHERE id=%s AND order_type=%s", (rid, kind), None)
    flash("பதிவு நீக்கப்பட்டது.", "ok")
    return redirect(url_for("listing", kind=kind))

# ---------- பட்டன் 2: பயன்படுத்த இயலாத நூல்கள் (4 படிகள்; இப்போது படி 1) ----------
CASE_SQL = """SELECT c.*, l.name lib_name, t.name type_name FROM condemn_cases c
              JOIN libraries l ON l.id=c.library_id JOIN library_types t ON t.id=c.library_type_id WHERE c.id=%s"""

def get_lib(lid):
    return run("""SELECT l.id, l.name, l.type_id, t.name type_name FROM libraries l
                  JOIN library_types t ON t.id=l.type_id WHERE l.id=%s""", (lid,), "one") or abort(404)

@app.route("/unusable/")
def unusable_home():
    return render_template("pick.html", types=run("SELECT id, name FROM library_types ORDER BY id"),
                           libs=run("SELECT id, name, type_id FROM libraries ORDER BY name"))

@app.route("/unusable/library/<int:lid>")
def unusable_library(lid):
    cases = run("SELECT * FROM condemn_cases WHERE library_id=%s ORDER BY id DESC", (lid,))
    return render_template("unusable_library.html", lib=get_lib(lid), cases=cases)

@app.route("/unusable/library/<int:lid>/step1", methods=["GET", "POST"])
@app.route("/unusable/case/<int:cid>/step1", methods=["GET", "POST"])
def step1(lid=None, cid=None):
    case = run("SELECT * FROM condemn_cases WHERE id=%s", (cid,), "one") if cid else None
    if cid and not case: abort(404)
    lib = get_lib(case["library_id"] if case else lid)
    if request.method == "POST":
        d = [val("file_no"), val("file_date"), val("letter_date"), val("inspector_date"),
             val("damaged_count", int), val("damaged_value")]
        if not (d[0] and d[1]):
            flash("கோப்பு எண், நாள் ஆகியவை கட்டாயம்.", "err")
        else:
            if case:
                run("""UPDATE condemn_cases SET s1_file_no=%s,s1_file_date=%s,s1_letter_date=%s,s1_inspector_date=%s,
                       s1_damaged_count=%s,s1_damaged_value=%s WHERE id=%s""", d + [cid], None)
            else:
                cid = run("""INSERT INTO condemn_cases(s1_file_no,s1_file_date,s1_letter_date,s1_inspector_date,
                             s1_damaged_count,s1_damaged_value,library_id,library_type_id)
                             VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""", d + [lib["id"], lib["type_id"]], "one")["id"]
            flash("படி 1 சேமிக்கப்பட்டது.", "ok")
            return redirect(url_for("unusable_case", cid=cid))
    return render_template("step1.html", lib=lib, row=case or {})

@app.route("/unusable/case/<int:cid>")
def unusable_case(cid):
    return render_template("case.html", c=run(CASE_SQL, (cid,), "one") or abort(404))

@app.route("/unusable/case/<int:cid>/step1.pdf")
def step1_pdf(cid):
    from condemn_pdf import build_condemn_step1
    c = run(CASE_SQL, (cid,), "one") or abort(404)
    try:
        data = build_condemn_step1(c)
    except AssertionError:
        flash("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை.", "err"); return redirect(url_for("unusable_case", cid=cid))
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=fname(c["lib_name"], "quotation callfor"))

# ---------- படி 2: விலைப்புள்ளி பரிசீலனை (அலுவலகக் குறிப்பு + ஆணை) ----------
@app.route("/unusable/case/<int:cid>/step2", methods=["GET", "POST"])
def step2(cid):
    c = run(CASE_SQL, (cid,), "one") or abort(404)
    if request.method == "POST":
        from decimal import Decimal
        d = [val("file_date"), val("total_weight", Decimal)]
        for i in (1, 2, 3):
            d += [val(f"q{i}_name"), val(f"q{i}_addr"), val(f"q{i}_rate", Decimal)]
        if d[0] is None or d[1] is None or any(d[2 + 3 * k] is None or d[4 + 3 * k] is None for k in range(3)):
            flash("நாள், மொத்த எடை, மூன்று விலைப்புள்ளிகளின் பெயர் மற்றும் ஒரு கிலோ விலை ஆகியவை கட்டாயம்.", "err")
            c = {**c, **{f"s2_{k}": v for k, v in request.form.items()}}
        else:
            run("""UPDATE condemn_cases SET s2_file_date=%s,s2_total_weight=%s,
                   s2_q1_name=%s,s2_q1_addr=%s,s2_q1_rate=%s,s2_q2_name=%s,s2_q2_addr=%s,s2_q2_rate=%s,
                   s2_q3_name=%s,s2_q3_addr=%s,s2_q3_rate=%s WHERE id=%s""", d + [cid], None)
            flash("படி 2 சேமிக்கப்பட்டது.", "ok")
            return redirect(url_for("unusable_case", cid=cid))
    return render_template("step2.html", c=c)

def _step2_pdf(cid, which):
    import condemn_step2_pdf as m
    c = run(CASE_SQL, (cid,), "one") or abort(404)
    if c["s2_file_date"] is None: abort(404)
    try:
        data = m.build_note(c) if which == "note" else m.build_order(c)
    except AssertionError:
        flash("ஆவணம் ஒரு பக்கத்தில் அடங்கவில்லை.", "err"); return redirect(url_for("unusable_case", cid=cid))
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True,
                     download_name=fname(c["lib_name"], "quotation note" if which == "note" else "sale order"))

@app.route("/unusable/case/<int:cid>/step2_note.pdf")
def step2_note_pdf(cid): return _step2_pdf(cid, "note")

@app.route("/unusable/case/<int:cid>/step2_order.pdf")
def step2_order_pdf(cid): return _step2_pdf(cid, "order")

if __name__ == "__main__":
    app.run(debug=True)
