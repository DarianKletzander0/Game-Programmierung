"""Generate the submitted PDF from docs/DOKUMENTATION.md."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "DOKUMENTATION.md"
OUTPUT = ROOT / "output" / "pdf" / "Signal_Breach_Dokumentation.pdf"

NAVY = colors.HexColor("#071126")
CYAN = colors.HexColor("#21DDEB")
BLUE = colors.HexColor("#3459A8")
MUTED = colors.HexColor("#536A7D")


class NumberedDocument(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=23 * mm,
            rightMargin=23 * mm,
            topMargin=22 * mm,
            bottomMargin=20 * mm,
            title="Signal Breach - Projektdokumentation",
            author="Einzelarbeit Game-Programmierung",
            subject="Dokumentation eines Computerspiels ohne Game Engine",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
        )
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._footer))

    @staticmethod
    def _footer(canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#C8D9E5"))
        canvas.line(23 * mm, 15 * mm, A4[0] - 23 * mm, 15 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(23 * mm, 10.5 * mm, "SIGNAL BREACH · PROJEKTDOKUMENTATION")
        canvas.drawRightString(A4[0] - 23 * mm, 10.5 * mm, f"SEITE {document.page}")
        canvas.restoreState()


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=34,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCustom",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=9,
        ),
        "h1": ParagraphStyle(
            "H1Custom",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=NAVY,
            spaceBefore=13,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2Custom",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.4,
            textColor=colors.HexColor("#172737"),
            spaceAfter=6,
            allowWidows=0,
            allowOrphans=0,
        ),
        "bullet": ParagraphStyle(
            "BulletCustom",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.8,
            leftIndent=12,
            firstLineIndent=-7,
            textColor=colors.HexColor("#172737"),
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "CodeCustom",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.4,
            leading=9.5,
            leftIndent=8,
            rightIndent=8,
            borderColor=colors.HexColor("#B8CCD9"),
            borderWidth=0.5,
            borderPadding=7,
            backColor=colors.HexColor("#F1F6F9"),
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=8,
        ),
    }


def inline_markup(text: str) -> str:
    value = escape(text.strip())
    parts = value.split("`")
    for index in range(1, len(parts), 2):
        parts[index] = f'<font name="Courier" color="#3459A8">{parts[index]}</font>'
    return "".join(parts)


def build_story(markdown: str) -> list:
    style = make_styles()
    lines = markdown.splitlines()
    section_start = next(
        index for index, line in enumerate(lines) if re.match(r"^## \d+\.", line)
    )
    title = lines[0].removeprefix("# ")
    subtitle = next(
        line.removeprefix("## ")
        for line in lines[1:section_start]
        if line.startswith("## ")
    )
    metadata = [
        line.strip().replace("  ", " ")
        for line in lines[1:section_start]
        if line.strip() and not line.startswith("## ")
    ]

    story: list = [
        Spacer(1, 54 * mm),
        Paragraph(inline_markup(title), style["title"]),
        Paragraph(inline_markup(subtitle), style["subtitle"]),
        Spacer(1, 14 * mm),
    ]
    story.extend(Paragraph(inline_markup(line), style["subtitle"]) for line in metadata)
    story.extend(
        [
            Spacer(1, 36 * mm),
            Paragraph(
                "PYTHON · PYGAME-CE · EIGENE GRAFIK · EIGENES AUDIO",
                style["subtitle"],
            ),
            PageBreak(),
        ]
    )

    paragraph: list[str] = []
    code: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(paragraph)), style["body"]))
            paragraph.clear()

    for raw_line in lines[section_start:]:
        line = raw_line.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code), style["code"], maxLineLength=88))
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if not line:
            flush_paragraph()
            continue
        if line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[3:]), style["h1"]))
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:]), style["h2"]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph("• " + inline_markup(line[2:]), style["bullet"]))
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            flush_paragraph()
            story.append(
                Paragraph(
                    f"{numbered.group(1)}. " + inline_markup(numbered.group(2)),
                    style["bullet"],
                )
            )
            continue
        paragraph.append(line.replace("  ", " "))

    flush_paragraph()
    if code:
        story.append(Preformatted("\n".join(code), style["code"], maxLineLength=88))
    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    markdown = SOURCE.read_text(encoding="utf-8")
    document = NumberedDocument(str(OUTPUT))
    document.build(build_story(markdown))
    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
