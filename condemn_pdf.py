"""பழுதடைந்த நூல்கள் - படி 1 ஆணை (ஒப்பப் புள்ளி கோர அனுமதி). A4, ஒரே பக்கம்."""
import os
from fpdf import FPDF
from order_pdf import FONT_DIR, dmy, num, clean_name

gen = lambda t: (t[:-2] + "த்தின்") if t.endswith("ம்") else t

def build_condemn_step1(r):
    for fs in (12, 11.5, 11, 10.5, 10, 9.5, 9):
        try:
            return _render(r, fs)
        except AssertionError:
            continue
    raise AssertionError("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை")

def _render(r, FS):
    lib, typ = clean_name(r["lib_name"]), r["type_name"]
    LH = FS * 0.55
    pdf = FPDF(orientation="P", unit="mm", format="A4"); pdf.set_auto_page_break(False)
    pdf.add_font("T", "", os.path.join(FONT_DIR, "NotoSansTamil-Regular.ttf"))
    pdf.add_font("T", "B", os.path.join(FONT_DIR, "NotoSansTamil-Bold.ttf"))
    pdf.set_text_shaping(True)
    L, R = 25, 20; pdf.set_margins(L, 16, R); pdf.add_page(); W = 210 - L - R
    nl = dict(new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("T", "B", 13)
    pdf.cell(W * 0.75, 8, "மாவட்ட நூலக அலுவலரின் செயல்முறைகள்,")
    pdf.cell(W * 0.25, 8, "திண்டுக்கல்", align="R", **nl); pdf.ln(3)
    pdf.set_font("T", "", FS)
    pdf.cell(W * 0.6, LH, f"ந.க.எண். {r['s1_file_no']}")
    pdf.cell(W * 0.4, LH, f"நாள் {dmy(r['s1_file_date'])}", **nl); pdf.ln(3)
    TX = L + 52; TW = 210 - R - TX
    def block(label, items, bold):
        y = pdf.get_y(); pdf.set_font("T", "B" if bold else "", FS); pdf.set_xy(L + 24, y); pdf.cell(26, LH, label)
        pdf.set_font("T", "", FS)
        for it in items:
            pdf.set_x(TX); pdf.multi_cell(TW, LH, it, align="J", **nl)
    block("பொருள்:", [f"பொது நூலகத்துறை – மாவட்ட நூலக ஆணைக்குழு திண்டுக்கல் – {typ},{lib} – மிகவும் பழுதடைந்து மீண்டும் பயன்படுத்த இயலாத நிலையிலுள்ள நூல்களை இருப்பு நீக்கம் செய்தல் – தொடர்பாக."], True)
    pdf.ln(1.5)
    block("பார்வை", [f"1.  நூலகர், {typ},{lib} கடித நாள் {dmy(r['s1_letter_date'])}",
                     f"2.  நூல் இருப்பு சரிபார்ப்பு அலுவலர் சான்று நாள் {dmy(r['s1_inspector_date'])}"], False)
    pdf.ln(2); pdf.cell(W, LH, "------------", align="C", **nl); pdf.ln(2)
    pdf.multi_cell(W, LH, "\u2003" * 4 + f"பார்வை 1 ல் காணும் {lib} {gen(typ)} நூலகர் கடிதத்தில் வேண்டிய கோரிக்கையை ஏற்று மேற்படி நூலகத்தில் மிகவும் பழுதடைந்து மீண்டும் கட்டுமானம் செய்ய இயலாமலும் வாசகர் பயன்பாட்டில் இருந்ததால் மீண்டும் பயன்படுத்த இயலாத நிலையில் உள்ள ரூ. {num(r['s1_damaged_value'])}/- மதிப்புடைய கிளைப் பதிவெண் {acc_from} முதல் {acc_to} முடிய உள்ள {num(r['s1_damaged_count'])} பழுதடைந்த நூல்களை ஏல விற்பனை செய்ய உரிய விதிமுறைப்படி மூன்று ஒப்பப் புள்ளிகள் பெற்று அனுப்பி வைக்க நூலகருக்கு அறிவுறுத்தப்படுகிறது.", align="J", **nl)
    pdf.ln(12); pdf.set_x(L + W * 0.55); pdf.set_font("T", "B", FS)
    pdf.multi_cell(W * 0.45, LH, "மாவட்ட நூலக அலுவலர்\nதிண்டுக்கல்", align="C", **nl)
    pdf.ln(4); pdf.set_x(L); pdf.cell(W, LH, "பெறுநர்", **nl)
    pdf.set_font("T", "", FS)
    for t in ("நூலகர்,", lib, typ): pdf.cell(W, LH, t, **nl)
    assert pdf.page == 1 and pdf.get_y() < 285
    return bytes(pdf.output())
