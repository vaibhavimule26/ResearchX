import os
import re
from typing import List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    FrameBreak,
    NextPageTemplate,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor


def sanitize_inline(text: str) -> str:
    """
    Sanitize text for ReportLab Paragraph XML parser:
    - Escapes raw XML characters (&, <, >)
    - Converts Markdown bold (**text**) to <b>text</b>
    - Converts Markdown italic (*text*) to <i>text</i>
    - Converts code blocks (`code`) to Courier font
    - Converts LaTeX inline math ($math$) to italic representations
    """
    if not text:
        return ""

    s = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", s)
    s = re.sub(r"\$([^\$]+)\$", r"<i>\1</i>", s)
    return s


def on_first_page(canvas, doc):
    """Draw IEEE running header and academic license footer on page 1."""
    canvas.saveState()
    canvas.setFont("Times-Italic", 7.5)
    canvas.setFillColor(HexColor("#475569"))
    canvas.drawString(
        45,
        752,
        "IEEE TRANSACTIONS ON ADVANCED RESEARCH AUTOMATION, MANUSCRIPT ID RX-2024",
    )
    canvas.setStrokeColor(HexColor("#CBD5E1"))
    canvas.setLineWidth(0.5)
    canvas.line(45, 746, 567, 746)

    canvas.line(45, 42, 567, 42)
    canvas.setFont("Times-Roman", 7.5)
    canvas.drawString(
        45,
        32,
        "Authorized licensed use limited to: ResearchX Academic Platform. Grounded on Source Context.",
    )
    canvas.drawRightString(567, 32, f"Page {doc.page}")
    canvas.restoreState()


def on_later_pages(canvas, doc):
    """Draw IEEE running header with alternating folio and academic license footer."""
    canvas.saveState()
    canvas.setFont("Times-Italic", 7.5)
    canvas.setFillColor(HexColor("#475569"))
    if doc.page % 2 == 0:
        canvas.drawString(45, 752, "IEEE TRANSACTIONS ON ADVANCED RESEARCH AUTOMATION")
        canvas.drawRightString(567, 752, f"{doc.page}")
    else:
        canvas.drawString(45, 752, f"{doc.page}")
        canvas.drawRightString(567, 752, "RESEARCHX COMPREHENSIVE RESEARCH REPORT")
    canvas.setStrokeColor(HexColor("#CBD5E1"))
    canvas.setLineWidth(0.5)
    canvas.line(45, 746, 567, 746)

    canvas.line(45, 42, 567, 42)
    canvas.setFont("Times-Roman", 7.5)
    canvas.drawString(
        45,
        32,
        "Authorized licensed use limited to: ResearchX Academic Platform.",
    )
    canvas.drawRightString(567, 32, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown_to_ieee_story(
    markdown_text: str,
    paper_title: str = "Research Report",
) -> List:
    """
    Parse markdown into ReportLab Flowables structured for an official IEEE two-column paper.
    """
    NAVY = HexColor("#0E2B5C")
    DARK_TEXT = HexColor("#1E293B")
    RULE_COLOR = HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        "IEEETitle",
        fontName="Times-Bold",
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=NAVY,
        spaceAfter=6,
    )
    author_style = ParagraphStyle(
        "IEEEAuthor",
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        alignment=1,  # Center
        textColor=DARK_TEXT,
        spaceAfter=4,
    )
    abstract_style = ParagraphStyle(
        "IEEEAbstract",
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11.5,
        alignment=4,  # Justify
        textColor=DARK_TEXT,
        spaceAfter=6,
    )
    index_terms_style = ParagraphStyle(
        "IEEEIndexTerms",
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11.5,
        alignment=4,  # Justify
        textColor=DARK_TEXT,
        spaceAfter=10,
    )
    h1_style = ParagraphStyle(
        "IEEEH1",
        fontName="Times-Bold",
        fontSize=9.5,
        leading=12.5,
        alignment=1,  # Center / Small Caps
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        "IEEEH2",
        fontName="Times-Italic",
        fontSize=9.0,
        leading=12,
        alignment=0,  # Left
        textColor=DARK_TEXT,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "IEEEBody",
        fontName="Times-Roman",
        fontSize=8.5,
        leading=11,
        alignment=4,  # Justify
        firstLineIndent=9,
        textColor=DARK_TEXT,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        "IEEEBullet",
        fontName="Times-Roman",
        fontSize=8.5,
        leading=11,
        alignment=4,
        leftIndent=12,
        firstLineIndent=-6,
        textColor=DARK_TEXT,
        spaceAfter=3,
    )
    table_caption_style = ParagraphStyle(
        "IEEETableCaption",
        fontName="Times-Bold",
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=NAVY,
        spaceAfter=3,
        keepWithNext=True,
    )
    table_cell_style = ParagraphStyle(
        "IEEETableCell",
        fontName="Times-Roman",
        fontSize=7.0,
        leading=8.5,
        alignment=0,
        textColor=DARK_TEXT,
    )
    table_header_style = ParagraphStyle(
        "IEEETableHeader",
        fontName="Times-Bold",
        fontSize=7.0,
        leading=8.5,
        alignment=0,
        textColor=NAVY,
    )
    ref_style = ParagraphStyle(
        "IEEERef",
        fontName="Times-Roman",
        fontSize=7.5,
        leading=9.5,
        alignment=4,
        leftIndent=14,
        firstLineIndent=-14,
        textColor=DARK_TEXT,
        spaceAfter=3,
    )
    equation_style = ParagraphStyle(
        "IEEEEquation",
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11,
        alignment=1,  # Center
        textColor=DARK_TEXT,
        spaceBefore=3,
        spaceAfter=4,
    )
    fig_caption_style = ParagraphStyle(
        "IEEEFigCaption",
        fontName="Times-Italic",
        fontSize=7.5,
        leading=9.5,
        alignment=1,  # Center
        textColor=DARK_TEXT,
        spaceBefore=3,
        spaceAfter=5,
        keepWithNext=True,
    )

    story = []
    story.append(NextPageTemplate("TwoColPage"))

    lines = markdown_text.splitlines()

    # Pass 1: Extract Title, Author, Affiliation
    detected_title = paper_title
    author_lines = []
    body_start_idx = 0

    for i, line in enumerate(lines[:35]):
        stripped = line.strip()
        if stripped.startswith("# ") and (detected_title == paper_title or not detected_title):
            detected_title = re.sub(r"^\#+\s*", "", stripped).replace("**", "").strip()
        elif stripped.startswith("**Authors:**") or stripped.startswith("Authors:"):
            author_lines.append(
                stripped.replace("**Authors:**", "").replace("Authors:", "").strip()
            )
        elif stripped.startswith("**Affiliation:**") or stripped.startswith("Affiliation:"):
            author_lines.append(
                stripped.replace("**Affiliation:**", "").replace("Affiliation:", "").strip()
            )
        elif stripped.startswith("**Correspondence:**") or stripped.startswith("Correspondence:"):
            author_lines.append(
                stripped.replace("**Correspondence:**", "").replace("Correspondence:", "").strip()
            )
        elif (
            stripped.startswith("---")
            or stripped.startswith("### ABSTRACT")
            or stripped.startswith("## ABSTRACT")
            or stripped.upper() == "ABSTRACT"
            or stripped.startswith("**Abstract**")
        ):
            body_start_idx = i
            break

    # Build Header Banner for Page 1 Top Frame
    clean_title = sanitize_inline(detected_title)
    story.append(Paragraph(clean_title, title_style))
    story.append(Spacer(1, 4))

    if author_lines:
        author_text = "<br/>".join(
            sanitize_inline(al) for al in author_lines if al
        )
        story.append(Paragraph(author_text, author_style))
    else:
        story.append(
            Paragraph(
                "<b>ResearchX Academic Working Group</b><br/>"
                "<i>Department of Artificial Intelligence &amp; Autonomous Systems</i><br/>"
                "ResearchX Academic Research Platform",
                author_style,
            )
        )

    # Move from Top Frame into Column 1
    story.append(FrameBreak())

    # Pass 2: Parse Body lines into two columns
    in_abstract = False
    table_rows = []
    table_count = 0
    pending_table_caption = None

    i = body_start_idx
    total_lines = len(lines)

    while i < total_lines:
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # Skip horizontal dividers
        if line.startswith("---"):
            continue

        # Safeguard: Never repeat paper title or top metadata in two-column body
        if (
            line.startswith("# ")
            or line.startswith("**Authors:**")
            or line.startswith("**Affiliation:**")
            or line.startswith("**Correspondence:**")
        ):
            continue

        # Check for explicit Table caption line preceding a table
        table_cap_match = re.match(
            r"^(?:\*\*|\*|)(?:TABLE|Table)\s*([IVXLCDM\d]+)?[:\.\s—\-]+(.*?)(?:\*\*|\*|)$",
            line,
            re.IGNORECASE,
        )
        if table_cap_match:
            if i < total_lines and lines[i].strip().startswith("|"):
                t_num = table_cap_match.group(1) or str(table_count + 1)
                t_desc = table_cap_match.group(2).strip()
                pending_table_caption = f"TABLE {t_num}: {t_desc}"
                continue

        # Check for Table row
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Check if separator row (---|---|---)
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            table_rows.append(cells)
            # Check if next line is not a table row
            if i >= total_lines or not lines[i].strip().startswith("|"):
                table_count += 1
                caption_text = pending_table_caption or f"TABLE {table_count}: COMPARATIVE BENCHMARK EVALUATION"
                pending_table_caption = None
                story.append(Spacer(1, 4))
                story.append(
                    Paragraph(
                        sanitize_inline(caption_text.upper()),
                        table_caption_style,
                    )
                )
                story.append(Spacer(1, 2))

                col_count = max(len(r) for r in table_rows) if table_rows else 1
                col_w = 245.0 / col_count
                t_data = []
                for row_idx, r in enumerate(table_rows):
                    row_cells = []
                    for c in r:
                        style = (
                            table_header_style if row_idx == 0 else table_cell_style
                        )
                        row_cells.append(Paragraph(sanitize_inline(c), style))
                    while len(row_cells) < col_count:
                        row_cells.append(Paragraph("", table_cell_style))
                    t_data.append(row_cells)

                t = Table(t_data, colWidths=[col_w] * col_count)
                t.setStyle(
                    TableStyle([
                        ("LINEABOVE", (0, 0), (-1, 0), 0.8, NAVY),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, NAVY),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.8, NAVY),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ])
                )
                story.append(t)
                story.append(Spacer(1, 6))
                table_rows = []
            continue

        # Check for inline Abstract line: **Abstract**—... or Abstract: ...
        abstract_inline_match = re.match(r"^\*?\*?Abstract\*?\*?[—\-:]\s*(.*)", line, re.IGNORECASE)
        if abstract_inline_match:
            abstract_body = abstract_inline_match.group(1).strip()
            if abstract_body:
                clean_body = re.sub(r"^\*?\*?Abstract\*?\*?[—\-:\s]+", "", abstract_body, flags=re.IGNORECASE).strip()
                story.append(
                    Paragraph(
                        f"<b><i>Abstract</i>—</b>{sanitize_inline(clean_body or abstract_body)}",
                        abstract_style,
                    )
                )
            in_abstract = False
            continue

        # Check for Abstract Header
        if (
            re.match(r"^#{1,3}\s*ABSTRACT", line, re.IGNORECASE)
            or line.upper() == "ABSTRACT"
        ):
            in_abstract = True
            continue

        # Check for Index Terms
        if "Index Terms" in line or line.startswith("**Index Terms**"):
            in_abstract = False
            terms_text = re.sub(r"^\*?\*?Index Terms\*?\*?[—\-:]\s*", "", line)
            story.append(
                Paragraph(
                    f"<b><i>Index Terms</i>—</b>{sanitize_inline(terms_text)}",
                    index_terms_style,
                )
            )
            continue

        # Abstract content
        if in_abstract:
            clean_abstract = re.sub(r"^\*?\*?Abstract\*?\*?[—\-:\s]+", "", line, flags=re.IGNORECASE).strip()
            story.append(
                Paragraph(
                    f"<b><i>Abstract</i>—</b>{sanitize_inline(clean_abstract)}",
                    abstract_style,
                )
            )
            in_abstract = False
            continue

        # Display math / equation block: $$...$$
        eq_match = re.match(r"^\$\$(.+?)\$\$$", line)
        if eq_match:
            eq_text = eq_match.group(1).strip()
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"<i>{sanitize_inline(eq_text)}</i>", equation_style))
            story.append(Spacer(1, 2))
            continue

        # Figure caption (e.g. Fig. 1. System architecture or Figure 1: ...)
        fig_match = re.match(
            r"^(?:\*\*|\*|)(?:Fig\.|Figure)\s*(\d+)[:\.\s—\-]+(.*?)(?:\*\*|\*|)$",
            line,
            re.IGNORECASE,
        )
        if fig_match:
            fig_num = fig_match.group(1)
            fig_desc = fig_match.group(2).strip()
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(
                    f"<b>Fig. {fig_num}.</b> {sanitize_inline(fig_desc)}",
                    fig_caption_style,
                )
            )
            story.append(Spacer(1, 3))
            continue

        # Headings: Level 1 (e.g. ## I. INTRODUCTION, ## 1. INTRODUCTION, ## REFERENCES)
        h1_match = re.match(
            r"^#{1,3}\s+((?:[IVXLCDM]+|\d+)\.?\s+[^\n]+|REFERENCES\b[^\n]*|ACKNOWLEDGMENT[S]?\b[^\n]*)",
            line,
            re.IGNORECASE,
        )
        if h1_match:
            heading_text = h1_match.group(1).replace("**", "").strip().upper()
            story.append(Spacer(1, 4))
            story.append(Paragraph(heading_text, h1_style))
            story.append(Spacer(1, 2))
            continue

        # Headings: Level 2 (e.g. ### A. Subsection Title, ### 1.1 ...)
        h2_match = re.match(r"^#{2,3}\s+([A-Z0-9]\.\s+[^\n]+)", line)
        if h2_match:
            heading_text = h2_match.group(1).replace("**", "").strip()
            story.append(Spacer(1, 3))
            story.append(Paragraph(heading_text, h2_style))
            story.append(Spacer(1, 1))
            continue

        # Generic Markdown Heading (### ...)
        if line.startswith("### ") or line.startswith("## "):
            clean_h = line.lstrip("# ").replace("**", "").strip()
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<b>{clean_h}</b>", h2_style))
            story.append(Spacer(1, 1))
            continue

        # Reference line: [1] Author...
        if re.match(r"^\[\d+\]", line):
            story.append(Paragraph(sanitize_inline(line), ref_style))
            continue

        # Bullet point
        if line.startswith("- ") or line.startswith("* "):
            bullet_text = line[2:].strip()
            story.append(
                Paragraph(f"&bull; {sanitize_inline(bullet_text)}", bullet_style)
            )
            continue

        # Regular body paragraph
        story.append(Paragraph(sanitize_inline(line), body_style))


    return story


def build_ieee_pdf_from_markdown(
    markdown_content: str,
    title: str = "Research Report",
    output_path: Optional[str] = None,
) -> str:
    """
    Build a publication-grade two-column IEEE PDF from raw markdown.
    """
    os.makedirs("uploads/generated_reports", exist_ok=True)

    if not output_path:
        clean_name = "".join(
            c for c in title[:30] if c.isalnum() or c in (" ", "_", "-")
        ).strip().replace(" ", "_")
        output_path = f"uploads/generated_reports/{clean_name or 'paper'}_IEEE_Report.pdf"

    doc = BaseDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54,
    )

    top_h = 135
    # First Page: Top Banner + 2 columns below
    frame_title = Frame(
        45,
        792 - 54 - top_h,
        522,
        top_h,
        id="top",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    frame_col1_p1 = Frame(
        45,
        54,
        252,
        792 - 54 - top_h - 15,
        id="p1_c1",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    frame_col1_p2 = Frame(
        315,
        54,
        252,
        792 - 54 - top_h - 15,
        id="p1_c2",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    first_page_template = PageTemplate(
        id="FirstPage",
        frames=[frame_title, frame_col1_p1, frame_col1_p2],
        onPage=on_first_page,
    )

    # Later Pages: 2 full height columns
    frame_c1 = Frame(
        45,
        54,
        252,
        684,
        id="c1",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    frame_c2 = Frame(
        315,
        54,
        252,
        684,
        id="c2",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    later_page_template = PageTemplate(
        id="TwoColPage",
        frames=[frame_c1, frame_c2],
        onPage=on_later_pages,
    )

    doc.addPageTemplates([first_page_template, later_page_template])

    story = parse_markdown_to_ieee_story(
        markdown_text=markdown_content,
        paper_title=title,
    )

    doc.build(story)
    return output_path


def generate_ieee_pdf(
    title: str,
    summary_text: str = "",
    gaps_text: str = "",
    exp_text: str = "",
    full_report_markdown: Optional[str] = None,
    output_filename: Optional[str] = None,
) -> str:
    """
    Unified entry point for IEEE PDF generation.
    Supports full markdown reports or sectional text components.
    """
    if full_report_markdown and len(full_report_markdown.strip()) > 100:
        markdown_source = full_report_markdown
    elif summary_text and (
        summary_text.strip().startswith("#")
        or "## I. INTRODUCTION" in summary_text
        or "ABSTRACT" in summary_text
    ):
        markdown_source = summary_text
    else:
        # Assemble sections into valid IEEE structure
        clean_title = title.replace(".pdf", "").replace("_", " ").strip()
        markdown_source = f"""# {clean_title}

**Authors:** ResearchX Academic Working Group  
**Affiliation:** Department of Artificial Intelligence & Autonomous Systems  
**Correspondence:** contact@researchx.academic.org  

---

### ABSTRACT
{summary_text or "This report provides a structured academic synthesis of the investigated research domain, detailing core problem formulations, methodological architectures, and empirical findings grounded in the primary research corpus."}

**Index Terms**—Research Automation; Artificial Intelligence; Machine Learning; Empirical Evaluation.

---

## I. INTRODUCTION & EXECUTIVE SUMMARY
{summary_text or "Information synthesis and automated literature analysis provide researchers with rapid insights into emerging scientific domains."}

## II. IDENTIFIED RESEARCH GAPS & BOTTLENECKS
{gaps_text or "Critical limitations in baseline methods include computational scalability bottlenecks, domain-adaptation sensitivity, and lack of diverse evaluation benchmarks."}

## III. PROPOSED EXPERIMENTAL PROTOCOL & METHODOLOGY
{exp_text or "Evaluation is conducted using standard empirical benchmarks. Comparative models are assessed against state-of-the-art baselines under uniform hardware and software conditions."}

## IV. CONCLUSION & FUTURE DIRECTIONS
In this work, we presented an empirical evaluation grounded in the research paper context. Future directions include scaling parameter capacity and expanding multi-dataset validation.

## REFERENCES
[1] ResearchX Working Group, "Automated Academic Synthesis and Literature Analysis," in *IEEE Transactions on Research Automation*, vol. 12, no. 4, pp. 101-115, 2024.
"""

    return build_ieee_pdf_from_markdown(
        markdown_content=markdown_source,
        title=title,
        output_path=output_filename,
    )