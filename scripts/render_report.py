from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, CondPageBreak, Flowable, Image, Paragraph, Spacer, Table, TableStyle

from layout import DEEP, BRIGHT, PALE, TEXT, MUTED, LINE, FONT_NAME, S, MODULE_TITLES, section_title, priority_label
from report_model import Report, SeedReportData, load_report

SEED_MODULE_TITLES = (
    "一、铺量目标与品牌号配合",
    "二、素人图文方向与选题",
    "三、种草帖示例",
    "四、从示例延展的选题",
    "五、对标账号参考",
)

PLATFORM_NAMES = {"xiaohongshu": "小红书", "douyin": "抖音"}
W = 174 * mm
TOP = A4[1] - 29 * mm
BOTTOM = 24 * mm
BODY = ParagraphStyle("CompactBody", parent=S["body"], leading=15.5, spaceBefore=0, spaceAfter=0)
SMALL = ParagraphStyle("Caption", parent=S["small"], fontSize=9, leading=12, wordWrap="CJK", spaceBefore=0, spaceAfter=0)
KICKER = S["section"]
LABEL = ParagraphStyle("LabelLeft", parent=BODY, textColor=DEEP, spaceAfter=0)
SUBHEAD = ParagraphStyle("Subheading", parent=BODY, fontSize=11.5, leading=16, textColor=DEEP, spaceBefore=2.5*mm, spaceAfter=1.5*mm, keepWithNext=True)
LEAD = ParagraphStyle("SectionLead", parent=SMALL, keepWithNext=True, spaceAfter=2*mm)


def esc(value):
    return escape(str(value))


def p(value, style=BODY):
    return Paragraph(esc(value), style)


def gap(height=3):
    return Spacer(1, height * mm)


def page_heading(section):
    return section_title(section)


def box(rows, widths, background=None, padding=5, repeat_rows=0):
    result = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=repeat_rows, splitByRow=1, splitInRow=1)
    settings = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("LINEBELOW", (0, 0), (-1, -2), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if background:
        settings.append(("BACKGROUND", (0, 0), (-1, -1), background))
    result.setStyle(TableStyle(settings))
    return result


def labeled(label, value):
    return box([[p(label, LABEL), p(value)]], [32*mm, W-32*mm])


def subhead(value):
    return p(value, SUBHEAD)


def data_table(headers, rows, widths, padding=5):
    table = box([[p(value, LABEL) for value in headers], *rows], widths, padding=padding, repeat_rows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE)]))
    return table


def _safe_image(path, max_width=43*mm, max_height=51*mm):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Screenshot not found: {path}")
    with PILImage.open(path) as check:
        check.verify()
    result = Image(str(path))
    scale = min(max_width/result.imageWidth, max_height/result.imageHeight)
    result.drawWidth = result.imageWidth * scale
    result.drawHeight = result.imageHeight * scale
    return result


def image_slot(path, label, width=43*mm, height=51*mm):
    if path:
        return _safe_image(path, width, height)
    cell = Table([[p(label, SMALL)]], colWidths=[width], rowHeights=[height])
    cell.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), PALE), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 10), ("RIGHTPADDING", (0,0), (-1,-1), 10)]))
    return cell


class RatioBar(Flowable):
    def __init__(self, pillars):
        super().__init__()
        self.pillars = pillars
        self.width, self.height = W, 11*mm

    def draw(self):
        x = 0
        shades = [DEEP, colors.HexColor("#5D9E3F"), BRIGHT, colors.HexColor("#B3DA93"), PALE]
        for index, item in enumerate(self.pillars):
            width = W * item.ratio / 100
            self.canv.setFillColor(shades[index])
            self.canv.rect(x, 0, width, self.height, stroke=0, fill=1)
            if width >= 11*mm:
                self.canv.setFillColor(colors.white if index < 2 else TEXT)
                self.canv.setFont(FONT_NAME, 10)
                self.canv.drawCentredString(x + width/2, 3.7*mm, f"{item.ratio}%")
            x += width


def path_row(steps):
    count = len(steps)
    if not count:
        return gap(0)
    arrow_width = 6*mm
    cell_width = (W-(count-1)*arrow_width)/count
    row, widths = [], []
    for index, step in enumerate(steps):
        if index:
            row.append(p("→", LABEL))
            widths.append(arrow_width)
        row.append(box([[p(step)]], [cell_width], PALE, 7))
        widths.append(cell_width)
    result = Table([row], colWidths=widths, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    return result


def _page_furniture(canvas, report, page, count, section):
    canvas.saveState()
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "momentum-mark.png"
    with PILImage.open(logo_path) as logo:
        logo_width_px, logo_height_px = logo.size
    logo_height = 10 * mm
    logo_width = logo_height * logo_width_px / logo_height_px
    logo_left = 18 * mm
    canvas.drawImage(str(logo_path), logo_left, A4[1] - 8*mm - logo_height,
                     width=logo_width, height=logo_height, mask="auto")
    brand_left = logo_left + logo_width + 2.5*mm
    canvas.setFillColor(DEEP)
    canvas.setFont(FONT_NAME, 11)
    canvas.drawString(brand_left, A4[1]-13*mm, "动量领航")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(brand_left, A4[1]-17*mm, "Momentum Pilot Technology")
    canvas.setFont(FONT_NAME, 8)
    label = "内部资料  /  版式示例" if report.sample_mode else "内部资料"
    canvas.drawRightString(A4[0]-18*mm, A4[1]-14*mm, label)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(.6)
    canvas.line(18*mm, A4[1]-21*mm, A4[0]-18*mm, A4[1]-21*mm)
    # A wrapping paragraph reserves space for the page number and date.
    footer = p(f"{report.client_company_name} · {PLATFORM_NAMES[report.platform]}", SMALL)
    _, h = footer.wrap(117*mm, 30)
    footer.drawOn(canvas, 18*mm, 15*mm)
    canvas.setFont(FONT_NAME, 8)
    canvas.drawRightString(A4[0]-18*mm, 16*mm, f"{report.generated_date}  |  {page}/{count}")
    canvas.setFont(FONT_NAME, 7)
    canvas.drawString(18*mm, 10*mm, "本报告由动量领航提供，仅供客户内部参考")
    canvas.restoreState()


def _sections(report):
    platform = PLATFORM_NAMES[report.platform]
    sections = []
    content = [p(report.client_company_name, S['brand_title']), gap(1),
               p('账号内容策略方案', S['title']), gap(1),
               *page_heading(MODULE_TITLES[0])]
    if report.sample_mode:
        content += [p('虚构版式示例：账号、数据、对标和选题仅用于演示。', SMALL), gap(2)]
    content += [subhead('1、账号昵称'), p(report.account_name), subhead('2、当前账号阶段')]
    profile = report.profile_screenshot
    note = report.profile_screenshot_note or ''
    # Some older cases stored the evidence-based judgment in the screenshot note.
    if note.startswith('阶段判断：'):
        judgment, note = note[len('阶段判断：'):], ''
    else:
        judgment = report.stage or '暂无法判断'
    rows = [
        [image_slot(profile, '主页截图暂未获取', 35*mm, 62*mm), p('粉丝量', LABEL), p(report.metrics.get('粉丝量') or '暂未获取')],
        ['', p('获赞与收藏', LABEL), p(report.metrics.get('获赞与收藏') or '暂未获取')],
        ['', p('简介', LABEL), p(report.account_bio or '暂未获取')],
        [p('现状判断', LABEL), p(judgment), ''],
    ]
    stage_table = Table(rows, colWidths=[42*mm, 32*mm, W-74*mm], hAlign='LEFT')
    stage_table.setStyle(TableStyle([
        ('SPAN', (0,0), (0,2)), ('SPAN', (1,3), (2,3)),
        ('GRID', (0,0), (-1,-1), .5, LINE), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'), ('NOSPLIT', (0,0), (-1,-1)),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    content.append(stage_table)
    if note:
        content.append(p(note, SMALL))
    content += [p(f'数据截取日期：{report.data_date}', SMALL),
                subhead('3、现有内容类型'), p('；'.join(report.current_content_types) or '暂未获取足够样本'),
                subhead('4、账号主要问题')]
    questions = {'定位': '能否快速看懂账号', '内容': '是否值得看、愿意分享', '表达': '标题、封面和视频是否有效', '转化': '能否带来咨询、购买或关注'}
    rows = []
    for item in report.diagnoses:
        kind = {'fact': '观察', 'inference': '推断', 'unknown': '待确认'}[item.evidence_type]
        rows.append([p(item.dimension, LABEL), p(questions[item.dimension], SMALL),
                     [p(item.conclusion), p(f'{kind}依据：{item.evidence}', SMALL)]])
    content += [data_table(['模块', '回答的问题', '结论与依据'], rows, [14*mm, 35*mm, W-49*mm]), gap(2),
                p(report.summary), subhead('5、本次方案核心方向'), box([[p(report.opportunity)]], [W], PALE)]
    sections.append((MODULE_TITLES[0], content))

    content = page_heading(MODULE_TITLES[1])
    if report.account_subject == 'person':
        content += [subhead('1、账号人设（IP定位）'), p(report.positioning), gap(2), box([
            [p('我是谁', LABEL), p(report.ip_profile.identity)],
            [p('我帮谁', LABEL), p(report.ip_profile.audience)],
            [p('我分享什么', LABEL), p(report.ip_profile.value)],
            [p('我怎么表达', LABEL), p(report.ip_profile.expression)],
        ], [30*mm, W-30*mm])]
    else:
        content += [subhead('1、账号定位'), p(report.positioning)]
    content += [gap(2), box([
        [p('目标用户', LABEL), p(report.target_audience)],
        [p(f'用户{report.goal}理由', LABEL), p(report.follow_reason)],
        [p('打造账号记忆点', LABEL), p(report.slogan or report.positioning)],
    ], [40*mm, W-40*mm])]
    if report.content_style:
        content += [p('表达风格：' + report.content_style, SMALL)]
    if report.optimization_logic:
        content += [subhead('2、优化逻辑'), p(' → '.join(report.optimization_logic))]
    rows = []
    for i, item in enumerate(report.problems, 1):
        rows.append([p(f'{i:02}', LABEL), [p(item.title + '：' + item.action), p('目的：' + item.impact, SMALL)], priority_label(item.priority)])
    content += [subhead('优化动作'), data_table(['先后', '动作与目的', '优先级'], rows, [14*mm, W-41*mm, 27*mm])]
    sections.append((MODULE_TITLES[1], content))

    content = page_heading(MODULE_TITLES[2]) + [p('以下比例为首轮内容测试建议，可依据实际表现调整。', LEAD)]
    rows = []
    for item in report.pillars:
        rows.append([[p(item.name, LABEL), p(f'{item.ratio}%')],
                     [p(item.purpose or '按账号目标补充具体任务'), p('栏目：' + ' / '.join(item.columns), SMALL)],
                     p(item.format or '根据素材条件确定', SMALL)])
    content += [data_table(['内容方向／占比', '内容任务与代表栏目', '建议形式'], rows, [38*mm, 94*mm, 42*mm])]
    sections.append((MODULE_TITLES[2], content))

    content = page_heading(MODULE_TITLES[3]) + [p(report.trend_note, LEAD)]
    counter = 0
    group_counter = 0
    for direction in report.topic_directions:
        selected = [item for item in report.topics if item.direction == direction]
        if not selected:
            continue
        group_counter += 1
        content += [subhead(f'{group_counter}、{direction}')]
        rows = []
        for item in selected:
            counter += 1
            rows.append([p(f'{counter:02}', SMALL), p(item.title), p(item.format, SMALL), priority_label(item.priority)])
        content += [data_table(['序号', '建议标题', '形式', '优先级'], rows, [12*mm, 109*mm, 26*mm, 27*mm], padding=4)]
    sections.append((MODULE_TITLES[3], content))

    sections.append(_benchmark_section(report))

    if report.conversion_path or report.production_loop:
        label = '六、' + report.closing_section_title
        content = page_heading(label)
        subsection_number = 1
        if report.conversion_path:
            content += [subhead(f'{subsection_number}、业务承接路径'), p(' → '.join(report.conversion_path))]
            subsection_number += 1
        if report.production_loop:
            content += [subhead(f'{subsection_number}、制作与复盘'), data_table(['顺序', '关键动作'],
                [[p(f'{i:02}', LABEL), p(step)] for i, step in enumerate(report.production_loop, 1)], [16*mm, W-16*mm])]
        sections.append((label, content))
    return sections


def _benchmark_section(report):
    content = page_heading(MODULE_TITLES[4])
    types = {'same_industry': '同赛道', 'same_stage': '相近阶段', 'format': '内容形式'}
    for i, item in enumerate(report.benchmarks, 1):
        role = '品牌自营 · ' if item.account_kind == 'brand' else ''
        content += [subhead(f'{i}、{item.name}  ·  {role}{types[item.benchmark_type]}')]
        details = [p('近期表现：' + (item.recent_performance or '暂未获取')),
                   p('内容分析：' + (item.content_analysis or '暂未获取')),
                   p('参考理由：' + item.reason), p('借鉴动作：' + item.learn),
                   p('不宜照搬：' + item.avoid, SMALL)]
        if item.screenshot:
            profile = [p('账号主页截图', SMALL), _safe_image(item.screenshot, 38*mm, 47*mm)]
            content += [box([[profile, details]], [46*mm, W-46*mm])]
        else:
            note = '虚构示例，未填入真实账号主页截图' if report.sample_mode else '账号主页截图暂未获取'
            content += [box([[details]], [W]), p(note, SMALL)]
    return MODULE_TITLES[4], content


def _seeding_sections(report: SeedReportData):
    intro, directions, examples, derived, _ = SEED_MODULE_TITLES
    platform = PLATFORM_NAMES[report.platform]
    content = [p(report.client_company_name, S['brand_title']), gap(1),
               p('素人图文种草方案', S['title']), *page_heading(intro)]
    if report.sample_mode:
        content += [p('虚构版式示例', SMALL), gap(2)]
    brief = [[p('项目目标', LABEL), p(report.goal)]]
    if report.target_audience:
        brief.append([p('目标用户', LABEL), p(report.target_audience)])
    scope = f'{platform}图文'
    if report.target_volume is not None:
        scope += f' · 计划 {report.target_volume} 篇'
    brief.append([p('投放规划', LABEL), p(scope)])
    if report.brand_support:
        brief.append([p('品牌号配合', LABEL), [p(action) for action in report.brand_support]])
    content.append(box(brief, [29*mm, W-29*mm]))
    sections = [(intro, content)]

    rows = []
    for i, item in enumerate(report.seeding_directions, 1):
        order = [p(f'{i:02}', LABEL)]
        if item.allocated_posts is not None:
            order.append(p(f'{item.allocated_posts}篇', SMALL))
        rows.append([order, [p(item.name, LABEL), p(item.audience_or_scene, SMALL)],
                     p(item.angle), [p(title) for title in item.titles]])
    content = page_heading(directions) + [
        data_table(['序号', '方向与适用场景', '图文切入点', '拟定标题'],
                   rows, [15*mm, 44*mm, 49*mm, W-108*mm])]
    sections.append((directions, content))

    content = page_heading(examples)
    for i, example in enumerate(report.seeding_examples, 1):
        caption = f'示例 {i}'
        if example.source_platform:
            caption += f' · {PLATFORM_NAMES[example.source_platform]}原帖'
        details = [p(caption, LABEL), gap(2), p('可借鉴做法', SMALL), p(example.takeaway)]
        content += [box([[_safe_image(example.screenshot, 68*mm, 102*mm), details]],
                        [74*mm, W-74*mm]), gap(1)]
    sections.append((examples, content))

    rows = []
    for topic in report.derived_topics:
        sources = '、'.join(str(n) for n in topic.example_numbers)
        rows.append([p(f'示例 {sources}', LABEL), p(topic.title), p(topic.angle)])
    content = page_heading(derived) + [
        data_table(['参考示例', '原创选题', '新切入点'], rows, [26*mm, 69*mm, W-95*mm])]
    sections.extend([(derived, content), _benchmark_section(report)])
    return sections


class NumberedCanvas(Canvas):
    def __init__(self, *args, report, **kwargs):
        super().__init__(*args, **kwargs)
        self.report = report
        self.saved_states = []

    def showPage(self):
        self.saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        count = len(self.saved_states)
        for state in self.saved_states:
            self.__dict__.update(state)
            _page_furniture(self, self.report, self._pageNumber, count, '')
            super().showPage()
        super().save()


def _allow_table_flow(story):
    """Keep headings with the first table row, while allowing the rest to split."""
    prepared = []
    index = 0
    while index < len(story):
        end = index
        while end < len(story) and story[end].getKeepWithNext():
            end += 1
        if end > index and end < len(story) and isinstance(story[end], Table):
            table = story[end]
            table.wrap(W, TOP-BOTTOM)
            header_rows = table.repeatRows if isinstance(table.repeatRows, int) else len(table.repeatRows)
            needed = sum(table._rowHeights[:header_rows+1])
            headings = story[index:end]
            for heading in headings:
                needed += heading.wrap(W, TOP-BOTTOM)[1] + heading.getSpaceBefore() + heading.getSpaceAfter()
                heading.keepWithNext = False
            prepared.append(CondPageBreak(min(needed, TOP-BOTTOM)))
            prepared.extend(headings)
            prepared.append(table)
            index = end+1
        else:
            prepared.append(story[index])
            index += 1
    return prepared


def build_flow_pdf(report, sections, output_path: Path, title=None) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buffer = BytesIO()
    doc = BaseDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                          topMargin=A4[1]-TOP, bottomMargin=BOTTOM,
                          title=title or f'{report.client_company_name}账号内容策略方案',
                          author='动量领航 / Momentum Pilot Technology', allowSplitting=1)
    frame = Frame(18*mm, BOTTOM, W, TOP-BOTTOM, id='body', leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='continuous', frames=[frame]))
    story = _allow_table_flow([item for _, items in sections for item in items])
    doc.build(story, canvasmaker=lambda *a, **kw: NumberedCanvas(*a, report=report, **kw))
    output_path.write_bytes(buffer.getvalue())
    return output_path


def render_report(report: Report, output_path: Path) -> Path:
    report.require_benchmark_review()
    if isinstance(report, SeedReportData):
        report.require_seeding_review()
        return build_flow_pdf(report, _seeding_sections(report), output_path,
                              title=f'{report.client_company_name}素人图文种草方案')
    return build_flow_pdf(report, _sections(report), output_path)


def main():
    parser = argparse.ArgumentParser(description="Render a standard Momentum Pilot account strategy report")
    parser.add_argument("report_json", type=Path)
    parser.add_argument("output_pdf", type=Path)
    args = parser.parse_args()
    render_report(load_report(args.report_json), args.output_pdf)


if __name__ == "__main__":
    main()
