from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image
from pypdf import PdfReader

from report_model import Report, SeedReportData, load_report
from render_report import SEED_MODULE_TITLES
from layout import MODULE_TITLES


@dataclass
class ValidationResult:
    errors: List[str]
    page_images: List[Path]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_output(pdf_path: Path, report: Report, preview_dir: Path) -> ValidationResult:
    errors: List[str] = []
    images: List[Path] = []
    pdf_path = Path(pdf_path)
    preview_dir = Path(preview_dir)

    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:
        return ValidationResult([f"PDF cannot be opened: {exc}"], [])

    if not reader.pages:
        errors.append("PDF contains no pages")
    for index, page in enumerate(reader.pages, 1):
        if float(page.mediabox.width) >= float(page.mediabox.height):
            errors.append(f"Page {index} is not portrait")

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    compact_text = re.sub(r"\s+", "", text)
    required = [
        "动量领航", "Momentum Pilot Technology", "内部资料",
        report.client_company_name,
        *[item.name for item in report.benchmarks],
        *[item.recent_performance for item in report.benchmarks if item.recent_performance],
        *[item.content_analysis for item in report.benchmarks if item.content_analysis],
    ]
    try:
        report.require_benchmark_review()
    except ValueError as exc:
        errors.append(str(exc))
    if isinstance(report, SeedReportData):
        titles = SEED_MODULE_TITLES
        try:
            report.require_seeding_review()
        except ValueError as exc:
            errors.append(str(exc))
        required.extend([report.goal, report.target_audience, *report.brand_support])
        if report.target_volume is not None:
            required.append(f'计划 {report.target_volume} 篇')
        for direction in report.seeding_directions:
            required.extend([direction.name, direction.audience_or_scene, direction.angle, *direction.titles])
        for topic in report.derived_topics:
            required.extend([topic.title, topic.angle, '示例 ' + '、'.join(map(str, topic.example_numbers))])
        embedded_sizes = {image.image.size for page in reader.pages for image in page.images}
        for i, example in enumerate(report.seeding_examples, 1):
            required.extend([f'示例 {i}', example.takeaway])
            try:
                with Image.open(example.screenshot) as screenshot:
                    size = screenshot.size
                    screenshot.verify()
                if size not in embedded_sizes:
                    errors.append(f'Original post screenshot missing from PDF: example {i}')
            except (OSError, ValueError) as exc:
                errors.append(f'Invalid original post screenshot for example {i}: {exc}')
    else:
        titles = MODULE_TITLES
        required.extend([report.account_name, *[item.title for item in report.topics]])
    required.extend(titles)
    for token in required:
        if re.sub(r"\s+", "", token) not in compact_text:
            errors.append(f"Required text missing: {token}")
    positions = [compact_text.find(title) for title in titles]
    if all(position >= 0 for position in positions) and positions != sorted(positions):
        errors.append("Report modules are out of order")

    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        errors.append("pdftoppm is not available")
        return ValidationResult(errors, images)

    preview_dir.mkdir(parents=True, exist_ok=True)
    prefix = preview_dir / "page"
    proc = subprocess.run([pdftoppm, "-png", "-r", "130", str(pdf_path), str(prefix)], capture_output=True, text=True)
    if proc.returncode != 0:
        errors.append(f"Page rendering failed: {proc.stderr.strip()}")
    else:
        images = sorted(preview_dir.glob("page-*.png"))
        if len(images) != len(reader.pages):
            errors.append(f"Rendered {len(images)} previews for {len(reader.pages)} pages")

    return ValidationResult(errors, images)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report_json", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("preview_dir", type=Path)
    args = parser.parse_args()
    result = validate_output(args.pdf, load_report(args.report_json), args.preview_dir)
    for error in result.errors:
        print(error)
    raise SystemExit(0 if result.ok else 1)


if __name__ == "__main__":
    main()

