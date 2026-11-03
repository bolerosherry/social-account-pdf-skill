from __future__ import annotations

import os
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


FONT_NAME = "MP-CJK"


def resolve_cjk_font(candidates=None) -> Path:
    if candidates is None:
        candidates = []
        configured = os.environ.get("MOMENTUM_PDF_FONT")
        if configured:
            candidates.append(Path(configured))
        candidates.extend([
            Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        ])
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    raise RuntimeError("No CJK font found. Set MOMENTUM_PDF_FONT to a readable TTF/TTC font path.")


FONT_PATH = resolve_cjk_font()
pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH)))

BRAND = json.loads((Path(__file__).resolve().parents[1] / "assets/brand.json").read_text())
DEEP = colors.HexColor(BRAND["deep_green"])
BRIGHT = colors.HexColor(BRAND["bright_green"])
PALE = colors.HexColor(BRAND["pale_green"])
TEXT = colors.HexColor(BRAND["text"])
MUTED = colors.HexColor(BRAND["muted"])
LINE = colors.HexColor(BRAND["line"])
LOW = colors.HexColor(BRAND["low_priority"])


def styles():
    base = getSampleStyleSheet()
    return {
        "brand_title": ParagraphStyle("BrandTitleCN", parent=base["Title"], fontName=FONT_NAME, fontSize=30, leading=38, textColor=TEXT, alignment=TA_CENTER, wordWrap="CJK"),
        "title": ParagraphStyle("TitleCN", parent=base["Title"], fontName=FONT_NAME, fontSize=22, leading=29, textColor=TEXT, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1CN", parent=base["Heading1"], fontName=FONT_NAME, fontSize=22, leading=28, textColor=TEXT),
        "section": ParagraphStyle("SectionCN", parent=base["Heading2"], fontName=FONT_NAME, fontSize=15, leading=20, textColor=DEEP, wordWrap="CJK", spaceBefore=4*mm, spaceAfter=2*mm, keepWithNext=True),
        "h2": ParagraphStyle("H2CN", parent=base["Heading2"], fontName=FONT_NAME, fontSize=12, leading=17, textColor=DEEP, spaceAfter=2*mm),
        "body": ParagraphStyle("BodyCN", parent=base["BodyText"], fontName=FONT_NAME, fontSize=11, leading=16.5, textColor=TEXT, wordWrap="CJK", spaceAfter=2.5*mm),
        "small": ParagraphStyle("SmallCN", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8.5, leading=12, textColor=MUTED),
        "metric": ParagraphStyle("MetricCN", parent=base["BodyText"], fontName=FONT_NAME, fontSize=13, leading=17, textColor=TEXT, alignment=TA_CENTER),
        "label": ParagraphStyle("LabelCN", parent=base["BodyText"], fontName=FONT_NAME, fontSize=8, leading=11, textColor=MUTED, alignment=TA_CENTER),
    }


S = styles()

MODULE_TITLES = ("一、账号诊断", "二、定位优化", "三、内容方向参考", "四、选题建议", "五、对标账号参考")


def section_title(title: str):
    return [Paragraph(escape(title), S["section"])]


def info_card(title: str, body: str, accent=DEEP):
    table = Table([[Paragraph(title, S["h2"]), Paragraph(body, S["body"])]], colWidths=[40*mm, 120*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def metric_grid(metrics: dict):
    items = list(metrics.items())[:6]
    cells = []
    for label, value in items:
        cells.append([Paragraph(escape(str(value)), S["metric"]), Paragraph(escape(str(label)), S["label"])])
    while len(cells) < 6:
        cells.append([Paragraph("-", S["metric"]), Paragraph("", S["label"])])
    rows = [[cells[i], cells[i+1], cells[i+2]] for i in range(0, 6, 3)]
    table = Table(rows, colWidths=[54*mm]*3, rowHeights=[25*mm]*2)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def priority_label(priority: str) -> Table:
    labels = {"high": "高优先级", "medium": "中优先级", "low": "低优先级"}
    colors_map = {"high": "#FFFFFF", "medium": "#315A22", "low": "#5F665F"}
    backgrounds = {"high": "#3F7E22", "medium": "#EAF4E5", "low": "#EEF1EE"}
    label = Paragraph(f'<font color="{colors_map[priority]}">{labels[priority]}</font>', S["small"])
    table = Table([[label]], colWidths=[20*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(backgrounds[priority])),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def spacer(height=4):
    return Spacer(1, height*mm)

