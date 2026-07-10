#!/usr/bin/env python3
"""Build the Markdown resume into an ATS-friendly PDF."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_WIDTH, PAGE_HEIGHT = A4
REPO_ROOT = Path(__file__).resolve().parents[1]
VENDORED_FONT_DIR = REPO_ROOT / "assets" / "fonts" / "liberation-sans"
LEFT_MARGIN = 56.7
RIGHT_MARGIN = 56.7
TOP_MARGIN = 53
BOTTOM_MARGIN = 48
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
FOOTER_TEXT = "Denis Glotov - resume - page {page} of {total}"
LINK_COLOR = "#2563eb"

# Markdown inline link: [label](url).
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Markdown bold span: **text**.
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
MARKDOWN_BULLETS = {1: "\u2022", 2: "\u25e6"}


def register_resume_fonts() -> dict[str, str]:
    font_files = {
        "regular": VENDORED_FONT_DIR / "LiberationSans-Regular.ttf",
        "bold": VENDORED_FONT_DIR / "LiberationSans-Bold.ttf",
        "italic": VENDORED_FONT_DIR / "LiberationSans-Italic.ttf",
        "bold_italic": VENDORED_FONT_DIR / "LiberationSans-BoldItalic.ttf",
    }
    if not all(path.exists() for path in font_files.values()):
        return {
            "regular": "Helvetica",
            "bold": "Helvetica-Bold",
            "italic": "Helvetica-Oblique",
            "bold_italic": "Helvetica-BoldOblique",
        }

    names = {
        "regular": "ResumeSans",
        "bold": "ResumeSans-Bold",
        "italic": "ResumeSans-Italic",
        "bold_italic": "ResumeSans-BoldItalic",
    }
    for key, path in font_files.items():
        pdfmetrics.registerFont(TTFont(names[key], str(path)))
    pdfmetrics.registerFontFamily(
        names["regular"],
        normal=names["regular"],
        bold=names["bold"],
        italic=names["italic"],
        boldItalic=names["bold_italic"],
    )
    return names


FONTS = register_resume_fonts()


class NumberedCanvas(canvas.Canvas):
    """Draw the footer after ReportLab knows the final page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, total_pages: int) -> None:
        self.saveState()
        self.setFillColor(colors.black)
        self.setFont(FONTS["regular"], 9)
        self.drawString(LEFT_MARGIN, 25, FOOTER_TEXT.format(
            page=self._pageNumber, total=total_pages))
        self.restoreState()


def inline_markup(text: str) -> str:
    """Convert the small Markdown inline subset used by the resume."""

    def convert_plain(chunk: str) -> str:
        escaped = html.escape(chunk, quote=False)
        return BOLD_RE.sub(r"<b>\1</b>", escaped)

    parts = []
    cursor = 0
    for match in LINK_RE.finditer(text):
        parts.append(convert_plain(text[cursor: match.start()]))
        label = convert_plain(match.group(1))
        url = html.escape(match.group(2), quote=True)
        parts.append(
            f'<a href="{url}"><font color="{LINK_COLOR}">{label}</font></a>'
        )
        cursor = match.end()
    parts.append(convert_plain(text[cursor:]))
    return "".join(parts)


def parse_markdown(markdown: str) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    intro_lines = 0
    seen_section = False
    expect_role = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if blocks and blocks[-1]["type"] == "paragraph":
                blocks.append({"type": "paragraph_break"})
            continue

        if stripped == "<!-- pagebreak -->":
            blocks.append({"type": "pagebreak"})
            expect_role = False
            continue

        if line.startswith("# "):
            blocks.append({"type": "title", "text": line[2:].strip()})
            continue

        if line.startswith("## "):
            seen_section = True
            expect_role = False
            blocks.append({"type": "section", "text": line[3:].strip()})
            continue

        if line.startswith("### "):
            seen_section = True
            expect_role = True
            heading = line[4:].strip()
            if " | " in heading:
                company, dates = heading.rsplit(" | ", 1)
            else:
                company, dates = heading, ""
            blocks.append(
                {
                    "type": "job",
                    "company": company.strip(),
                    "dates": dates.strip(),
                }
            )
            continue

        if line.startswith("  - "):
            blocks.append({"type": "bullet", "level": 2,
                          "text": line[4:].strip()})
            continue

        if line.startswith("- "):
            blocks.append({"type": "bullet", "level": 1,
                          "text": line[2:].strip()})
            continue

        if stripped.startswith("**Skills:**"):
            blocks.append({"type": "skills", "text": stripped})
            continue

        if not seen_section:
            if intro_lines == 0:
                block_type = "subtitle"
            elif intro_lines == 1:
                block_type = "contact"
            else:
                block_type = "summary"
            intro_lines += 1
            blocks.append({"type": block_type, "text": stripped})
            continue

        if expect_role:
            blocks.append({"type": "role", "text": stripped})
            expect_role = False
        else:
            blocks.append({"type": "paragraph", "text": stripped})

    return blocks


def make_styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "Base",
        fontName=FONTS["regular"],
        fontSize=11.1,
        leading=13.35,
        alignment=TA_LEFT,
        textColor=colors.black,
        spaceAfter=4,
    )
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base,
            fontSize=15.6,
            leading=19,
            alignment=TA_CENTER,
            spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base,
            fontSize=11.6,
            leading=13.8,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "Contact",
            parent=base,
            fontSize=10.2,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "summary": ParagraphStyle(
            "Summary",
            parent=base,
            fontSize=11.2,
            leading=13.8,
            spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base,
            fontName=FONTS["bold_italic"],
            fontSize=13.4,
            leading=15.8,
            textColor=colors.HexColor("#666666"),
            spaceBefore=8,
            spaceAfter=9,
        ),
        "company": ParagraphStyle(
            "Company",
            parent=base,
            fontName=FONTS["bold"],
            fontSize=11.2,
            leading=13.4,
            spaceAfter=0,
        ),
        "date": ParagraphStyle(
            "Date",
            parent=base,
            fontName=FONTS["bold"],
            fontSize=11.2,
            leading=13.4,
            alignment=TA_RIGHT,
            spaceAfter=0,
        ),
        "role": ParagraphStyle(
            "Role",
            parent=base,
            fontSize=11.2,
            leading=13.4,
            spaceAfter=2.4,
        ),
        "body": base,
        "bullet1": ParagraphStyle(
            "Bullet1",
            parent=base,
            leftIndent=35,
            bulletIndent=20,
            bulletFontName=FONTS["regular"],
            bulletFontSize=11.4,
            firstLineIndent=0,
            spaceAfter=1.4,
        ),
        "bullet2": ParagraphStyle(
            "Bullet2",
            parent=base,
            leftIndent=54,
            bulletIndent=40,
            bulletFontName=FONTS["regular"],
            bulletFontSize=15,
            firstLineIndent=0,
            spaceAfter=1,
        ),
        "skills": ParagraphStyle(
            "Skills",
            parent=base,
            fontSize=9.3,
            leading=10.9,
            spaceBefore=1,
            spaceAfter=11,
        ),
    }


def job_table(
    company: str,
    dates: str,
    styles: dict[str, ParagraphStyle],
) -> Table:
    table = Table(
        [
            [
                Paragraph(f"<b>{inline_markup(company)}</b>",
                          styles["company"]),
                Paragraph(f"<b>{inline_markup(dates)}</b>", styles["date"]),
            ]
        ],
        colWidths=[CONTENT_WIDTH - 158, 158],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    table.spaceBefore = 5.5
    table.spaceAfter = 0
    return table


def build_story(blocks: Iterable[dict[str, object]]) -> list[object]:
    styles = make_styles()
    story: list[object] = []
    block_list = list(blocks)
    index = 0

    while index < len(block_list):
        block = block_list[index]
        index += 1
        block_type = block["type"]
        if block_type == "paragraph_break":
            continue
        if block_type == "pagebreak":
            story.append(PageBreak())
            continue
        if block_type == "job":
            story.append(
                job_table(str(block["company"]), str(block["dates"]), styles)
            )
            continue
        if block_type == "bullet":
            level = int(block["level"])
            bullet_text = MARKDOWN_BULLETS[level]
            style_name = "bullet1" if level == 1 else "bullet2"
            story.append(
                Paragraph(
                    inline_markup(str(block["text"])),
                    styles[style_name],
                    bulletText=bullet_text,
                )
            )
            continue

        if block_type == "paragraph":
            lines = [inline_markup(str(block["text"]))]
            while (
                index < len(block_list)
                and block_list[index]["type"] == "paragraph"
            ):
                lines.append(inline_markup(str(block_list[index]["text"])))
                index += 1
            text = "<br/>".join(lines)
            story.append(Paragraph(text, styles["body"]))
            continue

        text = inline_markup(str(block["text"]))
        style_name = str(block_type)
        if style_name in styles:
            story.append(Paragraph(text, styles[style_name]))
        else:
            story.append(Paragraph(text, styles["body"]))

        if block_type == "title":
            story.append(Spacer(1, 2))

    return story


def build_pdf(source: Path, output: Path) -> None:
    blocks = parse_markdown(source.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Denis Glotov - Resume",
        author="Denis Glotov",
        subject="Senior Software Engineer resume",
    )
    doc.allowSplitting = 0
    doc.build(build_story(blocks), canvasmaker=NumberedCanvas)


def main(argv: list[str]) -> int:
    source = Path(argv[1]) if len(argv) > 1 else Path("resume.md")
    output = Path(argv[2]) if len(argv) > 2 else Path(
        "output/pdf/denis-glotov-resume.pdf")
    build_pdf(source, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
