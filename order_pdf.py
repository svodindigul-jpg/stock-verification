"""பயன்பாட்டு அடிப்படையில் தள்ளுபடி ஆணை - A4 portrait, ஒரே பக்கம்."""
import os, re
from fpdf import FPDF

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
dmy = lambda d: d.strftime("%d.%m.%Y") if d else "........"
num = lambda v: "........" if v is None else (str(v) if isinstance(v, int) else f"{float(v):,.2f}")

def clean_name(n):  # "கி05.வேடசந்தூர்" -> "வேடசந்தூர்"
    return re.sub(r"^(?:கி|ஊ)\d+\.\s*", "", n).strip()

def build_order(r):
    """r: stock_verifications row (+ lib_name, type_name). returns PDF bytes (எப்போதும் ஒரே பக்கம்)"""
    for fs in (11.5, 11, 10.5, 10, 9.5, 9):   # அடங்கவில்லையெனில் எழுத்தளவு தானாகக் குறையும்
        try:
            return _render(r, fs)
        except AssertionError:
            continue
    raise AssertionError("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை")

def _render(r, FS):
    lib = clean_name(r["lib_name"]); typ = r["type_name"]
    pf, pt = dmy(r["period_from"]), dmy(r["period_to"])
    sf, st = dmy(r["stat_period_from"]), dmy(r["stat_period_to"])
    tot = num(r["total_used_books"]); cnt = num(r["shortage_count"]); val = num(r["shortage_value"])

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_font("T", "", os.path.join(FONT_DIR, "NotoSansTamil-Regular.ttf"))
    pdf.add_font("T", "B", os.path.join(FONT_DIR, "NotoSansTamil-Bold.ttf"))
    pdf.set_text_shaping(True)          # தமிழ் எழுத்துக்கள் சரியாக வர
    L, R = 25, 20
    pdf.set_margins(L, 16, R); pdf.add_page()
    W = 210 - L - R
    LH = FS * 0.55
    ind = "\u2003" * 5

    pdf.set_font("T", "B", 13)
    pdf.cell(W, 8, "திண்டுக்கல் மாவட்ட நூலக அலுவலரின் செயல்முறைகள் திண்டுக்கல்", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("T", "", FS)
    pdf.cell(W * 0.6, LH, f"ந.க.எண். {r['file_no']}")
    pdf.cell(W * 0.4, LH, f"நாள் {dmy(r['file_date'])}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    TX = L + 52          # உரைப் பத்தி தொடக்கம்
    TW = 210 - R - TX
    def block(label, items):
        y = pdf.get_y()
        pdf.set_font("T", "B", FS); pdf.set_xy(L + 24, y); pdf.cell(26, LH, label)
        pdf.set_font("T", "", FS)
        for it in items:
            pdf.set_x(TX); pdf.multi_cell(TW, LH, it, align="J", new_x="LMARGIN", new_y="NEXT")
    block("பொருள்:-", [f"மாவட்ட நூலக ஆணைக்குழு, திண்டுக்கல் {typ} நாள் {pf} முதல் {pt} முடிய நூல் இருப்பு சரிபார்ப்பு - நூல்கள் பயன்பாட்டு அடிப்படையில் தள்ளுபடி – குறைவுபட்ட அனைத்து நூல்களும் தள்ளுபடி செய்து ஆணை பிறப்பித்தல் – தொடர்பு"])
    pdf.ln(1.5)
    block("பார்வை:-", [f"1.  நூல் இருப்பு சரிபார்ப்பு அறிக்கை நாள் {dmy(r['officer_report_date'])}",
                       "2.  அரசாணை (நிலை) எண்.211, நாள் 23.11.2005"])
    pdf.ln(2); pdf.set_x(L); pdf.cell(W, LH, "*****", align="C", new_x="LMARGIN", new_y="NEXT"); pdf.ln(2)

    def para(t):
        pdf.set_x(L); pdf.multi_cell(W, LH, ind + t, align="J", new_x="LMARGIN", new_y="NEXT"); pdf.ln(2.5)
    para(f"திண்டுக்கல் மாவட்ட நூலக ஆணைக்குழுவின் கீழ் செயல்படும் {lib} நூலகத்தில் {pf} முதல் {pt} முடிய இருப்பு சரிபார்ப்பு பணி நடைபெற்ற போது பார்வை 1ல் காணும் அறிக்கையின்படி ரூ. {val} மதிப்புள்ள {cnt} நூல்கள் குறைவு காணப்பட்டது.")
    para("பார்வை (2)ல் குறிப்பிட்டுள்ள அரசாணையின்படி வாசகர் பயன்பாடு அடிப்படையில் 1000 பயன்பாடு நூல்களுக்கு 3 நூல்கள் வீதம் தள்ளுபடி செய்ய ஆணை பிறப்பிக்கப்பட்டுள்ளது.")
    para(f"அதனடிப்படையிலும் புள்ளி விவர பதிவேடுகளின்படியும் {sf} நாள் முதல் {st} முடிய {tot} நூல்கள் இந்நூலகத்தில் வாசகர்களால் பயன்படுத்தப்பட்டுள்ளதால் வாசகர் பயன்பாடு அடிப்படையில் 1000 க்கு 3 நூல்கள் வீதம் நூல்கள் தள்ளுபடி செய்யலாம் என்பதைக் கருத்தில் கொண்டு. இந்நூலகத்தில் நூல் இருப்பு சரிபார்ப்பின்போது குறைவு காணப்பட்ட {cnt} நூல்களை நூல் இருப்பில் இருந்து நீக்கம் செய்து கொள்ள நூலகருக்கு அனுமதி ஆணை வழங்கப்படுகிறது.")
    para(f"நூலகர் குறைவு காணப்பட்ட {cnt} நூல்களையும் இருப்பு நீக்கம் செய்து விலகல் பதிவேட்டில் பதிவு செய்துவிட்டு அறிக்கை வாயிலாக சமர்ப்பிக்குமாறு அறிவுறுத்தப்படுகிறது.")

    pdf.ln(4); pdf.set_x(L + W * 0.55)
    pdf.multi_cell(W * 0.45, LH, "மாவட்ட நூலக அலுவலர்\nதிண்டுக்கல்.", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4); pdf.set_x(L); pdf.set_font("T", "B", FS); pdf.cell(W, LH, "பெறுநர்", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("T", "", FS); pdf.cell(W, LH, "நூலகர்", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(W, LH, lib, new_x="LMARGIN", new_y="NEXT")
    assert pdf.page == 1 and pdf.get_y() < 285, "ஆணை ஒரு பக்கத்தில் அடங்கவில்லை"
    return bytes(pdf.output())
