"""பழுதடைந்த நூல்கள் - படி 3: இருப்பு நீக்க அனுமதி ஆணை (விற்பனைத் தொகை செலுத்திய விவரம்). A4, ஒரே பக்கம்."""
from decimal import Decimal
from fpdf.fonts import FontFace
from order_pdf import dmy, num, clean_name
from condemn_step2_pdf import _pdf, gen, quotes, highest


def rs(v):
    return f"ரூ. {num(v)}"


def build_approve(r):
    """இருப்பு நீக்க அனுமதி ஆணை PDF bytes"""
    for fs in (12, 11.5, 11, 10.5, 10, 9.5, 9):
        try:
            return _render(r, fs)
        except AssertionError:
            continue
    raise AssertionError("ஆணை ஒரு பக்கத்தில் அடங்கவில்லை")


def _render(r, FS):
    lib, typ = clean_name(r["lib_name"]), r["type_name"]
    LH = FS * 0.55
    pdf = _pdf(); L, R = 25, 20; pdf.set_margins(L, 16, R); pdf.add_page(); W = 210 - L - R
    nl = dict(new_x="LMARGIN", new_y="NEXT")
    TX = L + 52; TW = 210 - R - TX

    # தொகைகள்: பாதி விலை (படி 3) + ஏலம் (எண்ணிக்கை - படி 1, தொகை - படி 2 அதிக விலைப்புள்ளி)
    top = highest(quotes(r))
    a_cnt, a_amt = r["s1_damaged_count"], (top["total"] if top else None)
    h_cnt, h_amt = r["s3_half_count"] or 0, Decimal(str(r["s3_half_amount"] or 0))
    t_cnt = (h_cnt + a_cnt) if a_cnt is not None else None
    t_amt = (h_amt + a_amt) if a_amt is not None else None
    acc_from, acc_to = num(r["s1_acc_from"]), num(r["s1_acc_to"])
    approvals = f"{dmy(r['s1_file_date'])} மற்றும் {dmy(r['s2_file_date'])}"

    pdf.set_font("T", "B", 13)
    pdf.cell(W * 0.75, 8, "மாவட்ட நூலக அலுவலரின் செயல்முறைகள்,")
    pdf.cell(W * 0.25, 8, "திண்டுக்கல்.", align="R", **nl); pdf.ln(3)
    pdf.set_font("T", "", FS)
    pdf.cell(W * 0.6, LH, f"ந.க.எண். {r['s1_file_no']}")
    pdf.cell(W * 0.4, LH, f"நாள் {dmy(r['s3_file_date'])}", **nl); pdf.ln(3)

    def block(label, items, bold):
        y = pdf.get_y(); pdf.set_font("T", "B" if bold else "", FS); pdf.set_xy(L + 24, y); pdf.cell(26, LH, label)
        pdf.set_font("T", "", FS)
        for it in items:
            pdf.set_x(TX); pdf.multi_cell(TW, LH, it, align="J", **nl)
    block("பொருள்:", [f"பொது நூலகத்துறை – மாவட்ட நூலக ஆணைக்குழு திண்டுக்கல் – {typ},{lib} – பழுதடைந்து மீண்டும் பயன்படுத்த இயலாத நிலையிலுள்ள நூல்கள் – இருப்பு நீக்கம் செய்து கொள்ள அனுமதி – தொடர்பாக."], True)
    pdf.ln(1.5)
    block("பார்வை", [f"1.  இவ்வலுவலக கடிதம் இதே ந.க.எண். {r['s1_file_no']} நாள் {approvals}",
                     f"2.  நூலகர், {typ},{lib} கடித நாள் {dmy(r['s3_letter_date'])}"], False)

    pdf.ln(5); pdf.set_font("T", "B", FS)
    y = pdf.get_y(); pdf.cell(W, LH, "ஆணை", **nl)
    pdf.line(L, y + LH, L + pdf.get_string_width("ஆணை"), y + LH); pdf.ln(2)
    pdf.set_font("T", "", FS)
    pdf.multi_cell(W, LH, "\u2003" * 4 + f"பார்வை 2ல் காணும் {lib} {gen(typ)} நூலகரின் கடிதத்தில் பார்வை 1ல் காணும் {approvals} நாளிட்ட செயல்முறைகளில் அனுமதி அளித்தவாறு பழுதடைந்து பயன்படுத்த இயலாத நிலையில் உள்ள கிளைப் பதிவெண் {acc_from} முதல் {acc_to} முடிய உள்ள {num(t_cnt)} எண்ணிக்கையிலான {rs(r['s1_damaged_value'])} மதிப்புள்ள நூல்களை விற்பனை செய்ய அனுமதிக்கப்பட்டு பின்வருமாறு தொகை வங்கி கணக்கில் செலுத்தப்பட்டுள்ளது என நுலகர் தெரிவித்துள்ளார்.", align="J", **nl)
    pdf.ln(2.5)

    # "நூல்கள்" நெடுவரிசை: தலைப்புச் சொல் உடையாத குறைந்தபட்ச அகலம்; மீதம் முழுவதும் "விவரம்" நெடுவரிசைக்கு
    PAD, HFS = 1.2, FS - 3
    pdf.set_font("T", "", FS - 1); w_nums = max(pdf.get_string_width(num(v)) for v in (h_cnt, a_cnt, t_cnt))
    pdf.set_font("T", "B", HFS); w_cnt = max(w_nums + 2 * PAD + 1.5, 12.0)
    while len(pdf.multi_cell(w_cnt - 2 * PAD, LH, "நூல்கள்", dry_run=True, output="LINES")) > 1:
        w_cnt += 0.5          # தலைப்புச் சொல் ஒரே வரியில் அடங்கும் வரை (குறைந்தபட்சம்)
    w_cnt += 1.0
    w_no, w_amt, w_date = 22, 31, 27
    cw = (w_no, W - w_no - w_cnt - w_amt - w_date, w_cnt, w_amt, w_date)
    pdf.set_font("T", "", FS - 1)
    with pdf.table(col_widths=cw, text_align=("CENTER", "LEFT", "RIGHT", "RIGHT", "CENTER"),
                   headings_style=FontFace(emphasis="BOLD", size_pt=HFS),
                   line_height=(FS - 1) * 0.5, padding=PAD, width=W) as t:
        h = t.row()
        for c in ("வ.எண்", "விவரம்", "நூல்கள்", "மதிப்பு", "செலுத்திய நாள்"):
            h.cell(c, align="C")
        row = t.row(); row.cell("1"); row.cell("பாதி விலைக்கு விற்கப்பட்ட நூல்கள்")
        row.cell(num(h_cnt)); row.cell(rs(h_amt)); row.cell(dmy(r["s3_half_paid_date"]) if r["s3_half_paid_date"] else "")
        row = t.row(); row.cell("2"); row.cell("ஏல முறையில் விற்கப்பட்ட நூல்கள்")
        row.cell(num(a_cnt)); row.cell(rs(a_amt)); row.cell(dmy(r["s3_auction_paid_date"]))
        row = t.row(); row.cell(""); row.cell("மொத்தம்", align="R")
        row.cell(num(t_cnt)); row.cell(rs(t_amt)); row.cell("")
    pdf.set_font("T", "", FS); pdf.ln(3)

    pdf.multi_cell(W, LH, "\u2003" * 4 + f"எனவே நூலகரின் கோரிக்கையை ஏற்று விற்பனை செய்யப்பட்ட  {lib} {gen(typ)}  கிளைப் பதிவெண் {acc_from} முதல் {acc_to} முடிய உள்ள {num(t_cnt)} எண்ணிக்கையிலான {rs(r['s1_damaged_value'])} மதிப்பிலான நூல்களை இருப்பில் இருந்து நீக்கம் செய்து நூல் விலகல் பதிவேட்டில் பதிவு செய்து கொள்ள நூலகருக்கு அனுமதி அளிக்கப்படுகிறது. பதிவு செய்த விவரத்தை உடன் சமர்ப்பிக்குமாறும் அறிவுறுத்தப்படுகிறது.", align="J", **nl)

    pdf.ln(10); pdf.set_x(L + W * 0.55); pdf.set_font("T", "B", FS)
    pdf.multi_cell(W * 0.45, LH, "மாவட்ட நூலக அலுவலர்\nதிண்டுக்கல்", align="C", **nl)
    pdf.ln(4); pdf.set_x(L); pdf.cell(W, LH, "பெறுநர்", **nl)
    pdf.set_font("T", "", FS)
    for t_ in ("நூலகர்,", typ, lib): pdf.cell(W, LH, t_, **nl)
    assert pdf.page == 1 and pdf.get_y() < 285
    return bytes(pdf.output())
