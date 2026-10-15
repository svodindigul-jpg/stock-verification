"""பழுதடைந்த நூல்கள் - படி 2: விலைப்புள்ளி பரிசீலனை (அலுவலகக் குறிப்பு + ஆணை). A4."""
import os
from decimal import Decimal
from fpdf import FPDF
from order_pdf import FONT_DIR, dmy, num, clean_name

gen = lambda t: (t[:-2] + "த்தின்") if t.endswith("ம்") else t


def quotes(r):
    """மூன்று விலைப்புள்ளிகள்: [{name, addr, rate, total}]; total = மொத்த எடை x ஒரு கிலோ விலை"""
    w = Decimal(str(r["s2_total_weight"] or 0))
    out = []
    for i in (1, 2, 3):
        rate = r.get(f"s2_q{i}_rate")
        rate = Decimal(str(rate)) if rate is not None else None
        out.append({"name": r.get(f"s2_q{i}_name") or "", "addr": r.get(f"s2_q{i}_addr") or "",
                    "rate": rate, "total": (w * rate).quantize(Decimal("0.01")) if rate is not None else None})
    return out


def highest(qs):
    """அதிக ஒரு கிலோ விலை அளித்தவர் (சம அளவெனில் முதலில் உள்ளவர்)"""
    ok = [q for q in qs if q["rate"] is not None]
    return max(ok, key=lambda q: q["rate"]) if ok else None


def who(q):
    """பெயர், முகவரி (முகவரி இருந்தால் மட்டும்)"""
    addr = " ".join((q.get("addr") or "").split())
    return f"{q['name']}, {addr}" if addr else q["name"]


def kg(v):  # 1250.500 -> "1,250.5"; 1250.000 -> "1,250"
    s = f"{Decimal(str(v)):,.3f}".rstrip("0").rstrip(".")
    return s or "0"


def _pdf():
    pdf = FPDF(orientation="P", unit="mm", format="A4"); pdf.set_auto_page_break(False)
    pdf.add_font("T", "", os.path.join(FONT_DIR, "NotoSansTamil-Regular.ttf"))
    pdf.add_font("T", "B", os.path.join(FONT_DIR, "NotoSansTamil-Bold.ttf"))
    pdf.set_text_shaping(True)
    return pdf


def _subject_refs(pdf, r, L, FS, LH, TX, TW):
    lib, typ = clean_name(r["lib_name"]), r["type_name"]
    nl = dict(new_x="LMARGIN", new_y="NEXT")

    def block(label, items, bold):
        y = pdf.get_y(); pdf.set_font("T", "B" if bold else "", FS); pdf.set_xy(L + 24, y); pdf.cell(26, LH, label)
        pdf.set_font("T", "", FS)
        for it in items:
            pdf.set_x(TX); pdf.multi_cell(TW, LH, it, align="J", **nl)
    block("பொருள்:", [f"பொது நூலகத்துறை – மாவட்ட நூலக ஆணைக்குழு திண்டுக்கல் – பழுதடைந்த நூல்கள் விற்பனை – {typ},{lib} – பழுதடைந்து மீண்டும் பயன்படுத்த இயலாத நிலையிலுள்ள நூல்களை விற்பனை செய்ய ஆணை வழங்குதல் – தொடர்பாக."], True)
    pdf.ln(1.5)
    block("பார்வை", [f"1.  இவ்வலுவலக கடிதம் இதே ந.க.எண். {r['s1_file_no']} நாள் {dmy(r['s1_file_date'])}",
                     f"2.  நூலகர், {typ},{lib} கடித நாள் {dmy(r['s1_letter_date'])}"], False)


def build_note(r):
    """அலுவலகக் குறிப்பு PDF bytes"""
    for fs in (12, 11.5, 11, 10.5, 10, 9.5, 9):
        try:
            return _render_note(r, fs)
        except AssertionError:
            continue
    raise AssertionError("அலுவலகக் குறிப்பு ஒரு பக்கத்தில் அடங்கவில்லை")


def _render_note(r, FS):
    lib, typ = clean_name(r["lib_name"]), r["type_name"]
    qs = quotes(r); top = highest(qs)
    LH = FS * 0.55
    pdf = _pdf(); L, R = 25, 20; pdf.set_margins(L, 16, R); pdf.add_page(); W = 210 - L - R
    nl = dict(new_x="LMARGIN", new_y="NEXT")
    TX = L + 52; TW = 210 - R - TX

    pdf.set_font("T", "B", 13)
    pdf.cell(W * 0.6, 8, "அ.கு சமர்ப்பிக்கப்படுகிறது")
    pdf.set_font("T", "", FS)
    pdf.cell(W * 0.4, 8, f"ந.க.எண். {r['s1_file_no']}", **nl); pdf.ln(3)
    _subject_refs(pdf, r, L, FS, LH, TX, TW)
    pdf.ln(4); pdf.set_font("T", "", FS)
    pdf.multi_cell(W, LH, "\u2003" * 4 + f"பார்வை 2ல் காணும் {lib} {gen(typ)} நூலகரின் கடிதத்தில் வாசகர்கள் நீண்ட நாட்கள் பயன்படுத்திய மிகவும் பழுதடைந்த மீண்டும் பயன்படுத்த இயலாத {num(r['s1_damaged_count'])} நூல்களை விற்பனை செய்ய மூன்று ஒப்பப்புள்ளிகள் பெறப்பட்டு அவைகளின் விவரம் கீழே விவரிக்கப்பட்டுள்ளது.", align="J", **nl)
    pdf.ln(2)
    pdf.set_x(L + 6); pdf.cell(W, LH, f"1.  மொத்த நூல்கள்  -  {num(r['s1_damaged_count'])}", **nl)
    pdf.set_x(L + 6); pdf.cell(W, LH, f"2.  நூல்களின் மொத்த எடை  -  {kg(r['s2_total_weight'])} கிலோ", **nl)
    pdf.ln(2)

    pdf.set_font("T", "", FS - 1)
    with pdf.table(col_widths=(24, 60, 38, 43), text_align=("CENTER", "LEFT", "RIGHT", "RIGHT"),
                   line_height=(FS - 1) * 0.5, padding=1.2, width=W) as t:
        h = t.row()
        for c in ("வ.எண்", "விலைப்புள்ளி அளித்தவர் பெயர் முகவரி", "ஒரு கிலோ விலை", "மொத்த விலை"):
            h.cell(c)
        for i, q in enumerate(qs, 1):
            row = t.row()
            row.cell(str(i)); row.cell(q["name"] + (("\n" + q["addr"]) if q["addr"] else ""))
            row.cell(f"ரூ. {num(q['rate'])}"); row.cell(f"ரூ. {num(q['total'])}")
    pdf.set_font("T", "", FS); pdf.ln(3)
    pdf.multi_cell(W, LH, "\u2003" * 4 + f"மேற்கண்ட விலைப்புள்ளிகளில் அதிக விலைப்புள்ளி அளித்த திருவாளர் {who(top)} என்பாருக்கு பழுதடைந்த நூல்களை விற்றுக் கொள்ள நூலகருக்கு அனுமதி அளிக்கலாமா என்பதற்கு ஆணை வேண்டி பணிந்தனுப்பப்படுகிறது.", align="J", **nl)
    pdf.ln(4); pdf.cell(W, LH, "ஆணைக்காக", **nl)
    assert pdf.page == 1 and pdf.get_y() < 285
    return bytes(pdf.output())


def build_order(r):
    """விற்பனை அனுமதி ஆணை PDF bytes"""
    for fs in (12, 11.5, 11, 10.5, 10, 9.5, 9):
        try:
            return _render_order(r, fs)
        except AssertionError:
            continue
    raise AssertionError("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை")


def _render_order(r, FS):
    lib, typ = clean_name(r["lib_name"]), r["type_name"]
    qs = quotes(r); top = highest(qs)
    LH = FS * 0.55
    pdf = _pdf(); L, R = 25, 20; pdf.set_margins(L, 16, R); pdf.add_page(); W = 210 - L - R
    nl = dict(new_x="LMARGIN", new_y="NEXT")
    TX = L + 52; TW = 210 - R - TX

    pdf.set_font("T", "B", 13)
    pdf.cell(W * 0.75, 8, "மாவட்ட நூலக அலுவலரின் செயல்முறைகள்,")
    pdf.cell(W * 0.25, 8, "திண்டுக்கல்.", align="R", **nl); pdf.ln(3)
    pdf.set_font("T", "", FS)
    pdf.cell(W * 0.6, LH, f"ந.க.எண். {r['s1_file_no']}")
    pdf.cell(W * 0.4, LH, f"நாள் {dmy(r['s2_file_date'])}", **nl); pdf.ln(3)
    _subject_refs(pdf, r, L, FS, LH, TX, TW)
    pdf.ln(5); pdf.set_font("T", "B", FS)
    y = pdf.get_y(); pdf.cell(W, LH, "ஆணை", **nl)
    pdf.line(L, y + LH, L + pdf.get_string_width("ஆணை"), y + LH); pdf.ln(2)
    pdf.set_font("T", "", FS)
    pdf.multi_cell(W, LH, "\u2003" * 4 + f"பார்வை 2ல் காணும் {lib} {gen(typ)} நூலகரின் கடிதத்துடன் இணைத்து சமர்ப்பித்த ஒப்பந்தப்புள்ளிகளின் பரிசீலனை செய்யப்பட்டு **--திருவாளர். {who(top)} என்பாருக்கு--** {lib} {gen(typ)} பழுதடைந்து பயன்படுத்த இயலாத நிலையில் உள்ள **--{num(r['s1_damaged_count'])} எண்ணிக்கையிலான {kg(r['s2_total_weight'])} கிலோ எடை உள்ள நூல்களை கிலோ ஒன்றுக்கு ரூ. {num(top['rate'])} வீதம் ரூ. {num(top['total'])} மதிப்பில்--** விற்பனை செய்து கொள்ள நூலகருக்கு கீழ்க்காணும் நிபந்தனைகளுக்குட்பட்டு அனுமதி அளிக்கப்படுகிறது.", align="J", markdown=True, **nl)
    pdf.ln(2.5)
    conds = ["விற்பனைத் தொகைக்கு அன்றைய தினமே இரசீது கொடுக்க வேண்டும்.",
             "விற்பனை செய்து முடித்த பின்னர் தொகையினை உடனடியாக வங்கியில் செலுத்த வேண்டும்.",
             "நூலகரால் விற்பனைக்கு சமர்ப்பிக்கப்பட்ட பட்டியலில் குறிப்பிட்ட எடைக்கு குறைவு ஏற்படாமல் இருத்தல் வேண்டும். எடைக்குறைவு ஏற்படும் நிகழ்வில் அதற்குரிய தொகையினை சம்பந்தப்பட்ட நூலகரிடமிருந்து வசூலிக்கப்படும் என அறிவுறுத்தப்படுகிறது.",
             "மேற்படி நிபந்தனைகளை மீறும் பட்சத்தில் சம்பந்தப்பட்ட பணியாளர் மீது ஒழுங்கு நடவடிக்கை தொடரப்படும் என அறிவுறுத்தப்படுகிறது."]
    for i, c in enumerate(conds, 1):
        y = pdf.get_y(); pdf.set_xy(L + 8, y); pdf.cell(8, LH, f"{i}.")
        pdf.set_x(L + 16); pdf.multi_cell(W - 16, LH, c, align="J", **nl); pdf.ln(1.2)
    pdf.ln(8); pdf.set_x(L + W * 0.55); pdf.set_font("T", "B", FS)
    pdf.multi_cell(W * 0.45, LH, "மாவட்ட நூலக அலுவலர்\nதிண்டுக்கல்.", align="C", **nl)
    pdf.ln(4); pdf.set_x(L); pdf.cell(W, LH, "பெறுநர்", **nl)
    pdf.set_font("T", "", FS)
    for t in ("நூலகர்,", typ, lib): pdf.cell(W, LH, t, **nl)
    assert pdf.page == 1 and pdf.get_y() < 285
    return bytes(pdf.output())
