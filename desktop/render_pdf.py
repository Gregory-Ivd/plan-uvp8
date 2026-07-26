# -*- coding: utf-8 -*-
"""PDF-версія бланка. Шрифт — системний Times New Roman, щоб збігалося з .docx."""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

FONT, FONT_B = "PlanSerif", "PlanSerif-Bold"
_registered = False

_CANDIDATES = [
    (r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\timesbd.ttf"),
    (r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\georgiab.ttf"),
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
]


def _register_fonts():
    global _registered
    if _registered:
        return
    for regular, bold in _CANDIDATES:
        if os.path.exists(regular) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont(FONT, regular))
            pdfmetrics.registerFont(TTFont(FONT_B, bold))
            _registered = True
            return
    raise RuntimeError(
        "Не знайдено жодного системного шрифта з кирилицею "
        "(Times New Roman, Georgia, Arial). PDF створити неможливо — "
        "скористайтесь форматом Word."
    )


COL_WIDTHS = [1.9 * cm, 2.7 * cm, 9.4 * cm, 2.7 * cm, 2.3 * cm]


def build(doc_model, path):
    _register_fonts()
    tpl = doc_model.tpl

    body = ParagraphStyle("body", fontName=FONT, fontSize=8.5, leading=10.5,
                          alignment=4, spaceAfter=0)
    body_c = ParagraphStyle("body_c", parent=body, alignment=1)
    head = ParagraphStyle("head", fontName=FONT_B, fontSize=8.5, leading=10.5, alignment=1)
    band_st = ParagraphStyle("band", fontName=FONT_B, fontSize=8.5, leading=10.5, alignment=0)
    label = ParagraphStyle("label", fontName=FONT, fontSize=8.5, leading=10.5, alignment=0)
    h1 = ParagraphStyle("h1", fontName=FONT_B, fontSize=12, leading=15, alignment=1,
                        spaceAfter=8)
    center = ParagraphStyle("center", fontName=FONT, fontSize=10, leading=13, alignment=1)
    tiny = ParagraphStyle("tiny", fontName=FONT, fontSize=6.5, leading=8, alignment=1)
    sign = ParagraphStyle("sign", fontName=FONT, fontSize=10, leading=16, alignment=0)

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.0 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                            title=tpl["doc_title"], author=doc_model.pib() or "")

    grid = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ])

    story = [Paragraph(tpl["doc_title"], h1)]

    pib = doc_model.title_line()
    story.append(Paragraph(f"<b>Засудженого</b> <u>{_esc(pib)}</u>", center))
    story.append(Paragraph("(прізвище, власне ім'я, по батькові (за наявності))", tiny))
    date_from, date_to = doc_model.period()
    story.append(Paragraph(
        f"<b>на період з</b> <u>{_esc(date_from) or '______________'}</u>"
        f" <b>по</b> <u>{_esc(date_to) or '______________'}</u>", center))
    story.append(Spacer(1, 8))

    need_label = (tpl.get("need_field") or {}).get("label", "Криміногенна потреба")
    total_w = sum(COL_WIDTHS)
    t0 = Table([[Paragraph(f"<b>{_esc(need_label)}</b>", head)],
                [Paragraph(_esc(doc_model.need.strip()), body)]], colWidths=[total_w])
    t0.setStyle(grid)
    story.extend([t0, Spacer(1, 6)])

    rows = [[Paragraph("<b>Мета/цілі</b>", head), Paragraph("<b>Цілі</b>", head),
             Paragraph("<b>Поступові заходи, здійснення яких дадуть змогу "
                       "зменшити/усунути актуальні фактори ризику</b>", head),
             Paragraph("<b>Термін виконання</b>", head),
             Paragraph("<b>Отриманий результат (виконано, внесено зміни)</b>", head)]]
    spans, band_rows = [], []

    def add_band(text):
        rows.append([Paragraph(f"<b>{_esc(text)}</b>", band_st), "", "", "", ""])
        idx = len(rows) - 1
        spans.append(("SPAN", (0, idx), (4, idx)))
        band_rows.append(idx)

    def add_block(goals, term, obstacles):
        rows.append(["", Paragraph("Проміжні цілі", label), Paragraph(_esc(goals), body),
                     Paragraph(_esc(term), body_c), ""])
        rows.append(["", "", "", "", ""])
        rows.append(["", Paragraph("Перепони та їх<br/>можливе вирішення", label),
                     Paragraph(_esc(obstacles), body), "", ""])
        rows.append(["", "", "", "", ""])

    for group, caption in (("during", "Наміри та плани засудженого під час відбування "
                                      "кримінального покарання"),
                           ("after", "Наміри та плани засудженого після звільнення")):
        specs = [s for s in tpl["sections"] if s["group"] == group]
        if not specs:
            continue
        add_band(caption)
        for spec in specs:
            data = doc_model.sections[spec["id"]]
            if data["skipped"] and not data["goals"].strip():
                continue
            add_band(f"{spec['number']}. {spec['title']}")
            add_block(data["goals"].strip(), data["term"].strip(), data["obstacles"].strip())

    table = Table(rows, colWidths=COL_WIDTHS, repeatRows=1)
    style = TableStyle(grid.getCommands() + spans)
    for idx in band_rows:
        style.add("BACKGROUND", (0, idx), (4, idx), colors.Color(0.94, 0.94, 0.94))
    table.setStyle(style)
    story.append(table)

    story.append(Spacer(1, 8))
    line = "______________________________________________   ____ ____________ 20___ р."
    for caption in ("(підпис, власне ім'я та прізвище начальника відділення СПС)",
                    "(підпис, власне ім'я та прізвище засудженого)"):
        story.append(Paragraph("План розробив " + line, sign))
        story.append(Paragraph(caption, tiny))

    concl = Table([[Paragraph("<b>Висновки щодо результатів реалізації індивідуального "
                              "плану виправлення та ресоціалізації</b>", head)],
                   [Paragraph("<br/><br/><br/>", body)]], colWidths=[total_w])
    concl.setStyle(grid)
    story.extend([Spacer(1, 6), KeepTogether(concl), Spacer(1, 8)])

    story.append(Paragraph("Начальник відділення СПС ______________________________   "
                           "____ ____________ 20___ р.", sign))
    story.append(Paragraph("(підпис, власне ім'я та прізвище)", tiny))
    story.append(Paragraph("Ознайомлений ___________________________________________   "
                           "____ ____________ 20___ р.", sign))
    story.append(Paragraph("(підпис, власне ім'я та прізвище засудженого)", tiny))

    doc.build(story)
    return path


def _esc(text):
    return (str(text or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("\n", "<br/>"))
