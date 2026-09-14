import os
import re
from typing import Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


# ==========================================================
# Brand & Academic Color Palette
# ==========================================================
COLOR_NAVY = RGBColor(15, 23, 42)          # #0F172A - Deep Slate Navy
COLOR_INDIGO = RGBColor(79, 70, 229)       # #4F46E5 - ResearchX Primary Indigo
COLOR_COBALT = RGBColor(37, 99, 235)       # #2563EB - IEEE Cobalt Blue
COLOR_VIOLET = RGBColor(124, 58, 237)      # #7C3AED - Royal Violet Accent
COLOR_SLATE_DARK = RGBColor(30, 41, 59)    # #1E293B - Card Header text
COLOR_BODY = RGBColor(51, 65, 85)          # #334155 - High Contrast Body Text
COLOR_MUTED = RGBColor(100, 116, 139)      # #64748B - Subtitles & Footers
COLOR_CARD_BG = RGBColor(255, 255, 255)    # #FFFFFF - Clean Solid Card Surface
COLOR_CARD_ALT = RGBColor(248, 250, 252)   # #F8FAFC - Soft Slate Card Surface
COLOR_BORDER = RGBColor(226, 232, 240)     # #E2E8F0 - Subtle 1pt Border
COLOR_BORDER_ACCENT = RGBColor(199, 210, 254) # #C7D2FE - Indigo Tinted Border
COLOR_BADGE_BG = RGBColor(238, 242, 255)   # #EEF2FF - Soft Indigo Pill Fill
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_SUCCESS = RGBColor(16, 185, 129)     # #10B981 - Green for gains/metrics
COLOR_AMBER = RGBColor(217, 119, 6)        # #D97706 - Amber for bottlenecks/challenges

FONT_FAMILY = "Calibri"


def _parse_raw_presentation(presentation_text: str) -> List[Dict]:
    slides = []
    first_slide_match = re.search(r"(?:={4,}\s*)?###\s*Slide\s*\d+\b", presentation_text, re.IGNORECASE)
    if first_slide_match:
        presentation_text = presentation_text[first_slide_match.start():]

    raw_blocks = re.split(r"(?:={4,}\s*)?###\s*Slide\s*\d+[:\-—]?\s*", presentation_text)

    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue

        title = ""
        category = "ACADEMIC RESEARCH PRESENTATION"
        takeaway = ""
        bullets = []
        speaker_notes = ""
        in_bullets = False
        in_notes = False

        for line in block.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("==="):
                continue

            if line_str.startswith("**Category:**"):
                category = line_str.replace("**Category:**", "").replace("**", "").strip().upper()
                in_bullets = False
                in_notes = False
                continue

            if line_str.startswith("**Slide Title:**"):
                title = line_str.replace("**Slide Title:**", "").replace("**", "").strip()
                in_bullets = False
                in_notes = False
                continue

            if line_str.startswith("**Takeaway:**"):
                takeaway = line_str.replace("**Takeaway:**", "").replace("**", "").strip()
                in_bullets = False
                in_notes = False
                continue

            if "Bullet Points" in line_str:
                in_bullets = True
                in_notes = False
                continue

            if "Speaker Notes" in line_str:
                in_bullets = False
                in_notes = True
                continue

            if in_bullets:
                cleaned_bullet = re.sub(r"^[\*\-•]\s*", "", line_str).strip()
                if cleaned_bullet:
                    bullets.append(cleaned_bullet)
            elif in_notes:
                speaker_notes += (" " if speaker_notes else "") + line_str
            else:
                if not title and not line_str.startswith("**"):
                    title = line_str

        if not title:
            title = f"Research Slide {len(slides) + 1}"

        slides.append({
            "title": title,
            "category": category,
            "takeaway": takeaway,
            "bullets": bullets,
            "speaker_notes": speaker_notes,
        })

    return slides


def _split_lead_in(bullet: str) -> Tuple[str, str]:
    match = re.match(r"^\*\*(.*?)\*\*:?\s*(.*)", bullet)
    if match:
        lead = match.group(1).strip()
        body = match.group(2).strip()
        # Clean any informal 'Key Insight' / 'Key Takeaway' label
        lead = re.sub(r"^(?:Key\s+Insights?|Insight)\b", "Core Finding", lead, flags=re.IGNORECASE).strip()
        lead = re.sub(r"^(?:Key\s+Takeaways?|Takeaway)\b", "Empirical Deliverable", lead, flags=re.IGNORECASE).strip()
        if not lead.endswith(":"):
            lead += ":"
        return f"{lead} ", body

    if ":" in bullet:
        parts = bullet.split(":", 1)
        if len(parts[0].split()) <= 4:
            clean_first = parts[0].strip()
            clean_first = re.sub(r"^(?:Key\s+Insights?|Insight)\b", "Core Finding", clean_first, flags=re.IGNORECASE).strip()
            clean_first = re.sub(r"^(?:Key\s+Takeaways?|Takeaway)\b", "Empirical Deliverable", clean_first, flags=re.IGNORECASE).strip()
            return f"{clean_first}: ", parts[1].strip()

    return "", bullet


def _add_paragraph_runs(p, lead: str, body: str, bullet_color: RGBColor = COLOR_INDIGO, font_size: Pt = Pt(13.5)):
    p.space_after = Pt(8)
    p.line_spacing = 1.2

    b_run = p.add_run()
    b_run.text = "•  "
    b_run.font.name = FONT_FAMILY
    b_run.font.size = font_size
    b_run.font.bold = True
    b_run.font.color.rgb = bullet_color

    if lead:
        l_run = p.add_run()
        l_run.text = lead
        l_run.font.name = FONT_FAMILY
        l_run.font.size = font_size
        l_run.font.bold = True
        l_run.font.color.rgb = COLOR_NAVY

    b_text_run = p.add_run()
    b_text_run.text = body
    b_text_run.font.name = FONT_FAMILY
    b_text_run.font.size = font_size
    b_text_run.font.color.rgb = COLOR_BODY



def _is_insight_summary_slide(slide: Dict) -> bool:
    """
    Detect if a slide is a dedicated 'Key Insights', 'Key Takeaways',
    or similar informal summary slide.
    """
    title_clean = slide.get("title", "").strip()
    cat_clean = slide.get("category", "").strip().upper()

    insight_patterns = [
        r"\bkey\s+insights?\b",
        r"\bkey\s+takeaways?\b",
        r"\bexecutive\s+insights?\b",
        r"\bcore\s+takeaways?\b",
        r"\bmain\s+insights?\b",
        r"\bsummary\s+of\s+insights?\b",
        r"\binsights?\s*(?:&|and)\s*takeaways?\b",
    ]

    for pat in insight_patterns:
        if re.search(pat, title_clean, re.IGNORECASE):
            return True
        if re.search(pat, cat_clean, re.IGNORECASE):
            return True

    return False


def _find_target_slide_for_bullet(bullet: str, slides: List[Dict]) -> Optional[Dict]:
    """
    Map an insight bullet to the most relevant existing academic slide:
    Results, Gap/Limitations, Architecture/Methodology, or Conclusion/Roadmap.
    """
    b_lower = bullet.lower()

    # 1. Results / Empirical Evaluation / Performance
    results_keywords = [
        "accuracy", "f1", "bleu", "latency", "performance", "result",
        "outperform", "baseline", "metric", "score", "gain", "benchmark",
        "evaluation", "ablation", "percent", "%", "speedup", "boost",
    ]
    if any(kw in b_lower for kw in results_keywords):
        for s in slides:
            s_title = s.get("title", "").upper()
            s_cat = s.get("category", "").upper()
            if any(k in s_title or k in s_cat for k in ["RESULT", "EMPIRICAL", "EVALUATION", "PERFORMANCE", "BENCHMARK"]):
                return s

    # 2. Research Gap / Limitations / Bottlenecks
    gap_keywords = [
        "gap", "limitation", "bottleneck", "challenge", "unaddressed",
        "prior work", "constraint", "shortcoming", "overhead",
    ]
    if any(kw in b_lower for kw in gap_keywords):
        for s in slides:
            s_title = s.get("title", "").upper()
            s_cat = s.get("category", "").upper()
            if any(k in s_title or k in s_cat for k in ["GAP", "LIMITATION", "RELATED WORK", "LANDSCAPE"]):
                return s

    # 3. Methodology / System Architecture / Pipeline
    method_keywords = [
        "architecture", "method", "algorithm", "pipeline", "framework",
        "model", "loss", "dynamic", "topology", "ingestion", "consensus", "complexity",
    ]
    if any(kw in b_lower for kw in method_keywords):
        for s in slides:
            s_title = s.get("title", "").upper()
            s_cat = s.get("category", "").upper()
            if any(k in s_title or k in s_cat for k in ["ARCHITECTURE", "TECHNICAL", "IMPLEMENTATION", "METHOD", "PIPELINE"]):
                return s

    # 4. Future Scope / Conclusion / Roadmap
    future_keywords = [
        "future", "scope", "roadmap", "vision", "next step", "extension",
        "conclusion", "deliverable", "deployed",
    ]
    if any(kw in b_lower for kw in future_keywords):
        for s in slides:
            s_title = s.get("title", "").upper()
            s_cat = s.get("category", "").upper()
            if any(k in s_title or k in s_cat for k in ["CONCLUSION", "FUTURE", "ROADMAP", "LIMITATION"]):
                return s

    # Fallback: Prefer Conclusion or Results slide
    for s in reversed(slides):
        s_title = s.get("title", "").upper()
        s_cat = s.get("category", "").upper()
        if any(k in s_title or k in s_cat for k in ["CONCLUSION", "RESULT", "FINDING", "CONTRIBUTION"]):
            return s

    return slides[-1] if slides else None


def _is_duplicate_bullet(new_bullet: str, existing_bullets: List[str]) -> bool:
    """
    Check if a bullet point already has high overlap with an existing bullet
    to avoid redundant duplication.
    """
    def normalize(text: str) -> set:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        words = set(cleaned.split())
        return {w for w in words if len(w) > 3}

    new_words = normalize(new_bullet)
    if not new_words:
        return False

    for eb in existing_bullets:
        eb_words = normalize(eb)
        if not eb_words:
            continue
        intersection = new_words.intersection(eb_words)
        overlap_ratio = len(intersection) / max(len(new_words), 1)
        if overlap_ratio >= 0.70:
            return True

    return False


def _filter_and_merge_insight_slides(slides: List[Dict]) -> List[Dict]:
    """
    Remove all 'Key Insights' or 'Key Takeaways' slides from the deck
    and merge any non-duplicate findings into appropriate academic slides.
    """
    academic_slides = []
    insight_slides = []

    for s in slides:
        if _is_insight_summary_slide(s):
            insight_slides.append(s)
        else:
            academic_slides.append(s)

    if not insight_slides:
        return academic_slides

    if not academic_slides:
        return slides

    for i_slide in insight_slides:
        for b in i_slide.get("bullets", []):
            cleaned_b = re.sub(r"^\*\*(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway)\*\*:\s*", "", b, flags=re.I).strip()
            cleaned_b = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway):\s*", "", cleaned_b, flags=re.I).strip()

            target = _find_target_slide_for_bullet(cleaned_b, academic_slides)
            if target and not _is_duplicate_bullet(cleaned_b, target.get("bullets", [])):
                if not cleaned_b.startswith("**"):
                    cleaned_b = f"**Empirical Finding:** {cleaned_b}"
                target["bullets"].append(cleaned_b)

        # Merge unique takeaway
        i_takeaway = i_slide.get("takeaway", "").strip()
        if i_takeaway:
            cleaned_takeaway = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway):\s*", "", i_takeaway, flags=re.I).strip()
            target = _find_target_slide_for_bullet(cleaned_takeaway, academic_slides)
            if target and not _is_duplicate_bullet(cleaned_takeaway, target.get("bullets", [])):
                target["bullets"].append(f"**Empirical Finding:** {cleaned_takeaway}")

        # Merge speaker notes if unique
        i_notes = i_slide.get("speaker_notes", "").strip()
        if i_notes:
            for s in academic_slides:
                if any(k in s.get("title", "").upper() for k in ["RESULT", "CONCLUSION", "FINDING"]):
                    if i_notes not in s.get("speaker_notes", ""):
                        s["speaker_notes"] = (s.get("speaker_notes", "") + " " + i_notes).strip()
                    break

    return academic_slides


def _sanitize_slide_titles_and_subtitles(slides: List[Dict]):
    """
    Sanitize titles, categories, subtitles, and bullets across all slides
    to eliminate 'Key Insight' / 'Key Takeaways' phrasing.
    """
    for s in slides:
        title = s.get("title", "")
        title = re.sub(r"\bAblation\s+Insights\b", "Ablation Studies", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*[-–—:]*\s*(?:Key\s+Insights?|Key\s+Takeaways?)\b", "", title, flags=re.IGNORECASE).strip()
        title = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?)\s*[-–—:]*\s*", "", title, flags=re.IGNORECASE).strip()
        if not title:
            title = "Academic Evaluation & Findings"
        s["title"] = title

        cat = s.get("category", "")
        cat = re.sub(r"\b(?:KEY\s+INSIGHTS?|KEY\s+TAKEAWAYS?)\b", "EMPIRICAL EVALUATION", cat, flags=re.IGNORECASE).strip()
        s["category"] = cat

        sub = s.get("takeaway", "")
        sub = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway):\s*", "", sub, flags=re.IGNORECASE).strip()
        s["takeaway"] = sub

        new_bullets = []
        for b in s.get("bullets", []):
            b_clean = re.sub(r"^\*\*(?:Key\s+Insights?|Insight)\*\*:\s*", "**Core Finding:** ", b, flags=re.IGNORECASE)
            b_clean = re.sub(r"^\*\*(?:Key\s+Takeaways?|Takeaway)\*\*:\s*", "**Empirical Deliverable:** ", b_clean, flags=re.IGNORECASE)
            b_clean = re.sub(r"^(?:Key\s+Insights?|Insight):\s*", "Core Finding: ", b_clean, flags=re.IGNORECASE)
            b_clean = re.sub(r"^(?:Key\s+Takeaways?|Takeaway):\s*", "Empirical Deliverable: ", b_clean, flags=re.IGNORECASE)
            new_bullets.append(b_clean)
        s["bullets"] = new_bullets


def _setup_slide_base(slide, category: str, title: str, takeaway: str, index: int, total_slides: int, paper_title: str):
    # 1. Top Decorative Accent Rule
    accent = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0), Inches(0), Inches(13.333), Inches(0.12)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_INDIGO
    accent.line.fill.background()

    # 2. Category Kicker
    cat_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.35), Inches(11.533), Inches(0.28))
    cat_tf = cat_box.text_frame
    cat_tf.word_wrap = True
    cat_tf.margin_left = cat_tf.margin_right = cat_tf.margin_top = cat_tf.margin_bottom = 0
    p_cat = cat_tf.paragraphs[0]
    p_cat.text = category.upper()
    p_cat.font.name = FONT_FAMILY
    p_cat.font.size = Pt(10)
    p_cat.font.bold = True
    p_cat.font.color.rgb = COLOR_INDIGO

    # 3. Slide Title
    title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.65), Inches(11.533), Inches(0.68))
    title_tf = title_box.text_frame
    title_tf.word_wrap = True
    title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0
    p_title = title_tf.paragraphs[0]
    p_title.text = title
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(23)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_NAVY

    # 4. Slide Subtitle / Scope (No 'Key Insight' label)
    sub_text = takeaway or "Empirical findings, technical architecture, and validation from the research."
    sub_text = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway):\s*", "", sub_text, flags=re.IGNORECASE).strip()

    if sub_text:
        sub_box = slide.shapes.add_textbox(Inches(0.9), Inches(1.38), Inches(11.533), Inches(0.35))
        sub_tf = sub_box.text_frame
        sub_tf.word_wrap = True
        sub_tf.margin_left = sub_tf.margin_right = sub_tf.margin_top = sub_tf.margin_bottom = 0
        p_sub = sub_tf.paragraphs[0]
        r_txt = p_sub.add_run()
        r_txt.text = sub_text
        r_txt.font.name = FONT_FAMILY
        r_txt.font.size = Pt(12)
        r_txt.font.italic = True
        r_txt.font.color.rgb = COLOR_MUTED

    # 5. Bottom Divider Rule
    divider = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0.9), Inches(6.82), Inches(11.533), Pt(0.75)
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_BORDER
    divider.line.fill.background()

    # 6. Bottom Footer & Page Numbering
    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.92), Inches(11.533), Inches(0.35))
    foot_tf = foot_box.text_frame
    foot_tf.word_wrap = True
    foot_tf.margin_left = foot_tf.margin_right = foot_tf.margin_top = foot_tf.margin_bottom = 0
    p_foot = foot_tf.paragraphs[0]

    r_left = p_foot.add_run()
    r_left.text = "ResearchX Academic Automation Platform  |  College Final-Year Project Presentation"
    r_left.font.name = FONT_FAMILY
    r_left.font.size = Pt(9)
    r_left.font.color.rgb = COLOR_MUTED

    clean_title = (paper_title or "Research Presentation").replace(".pdf", "")[:45]
    r_center = p_foot.add_run()
    r_center.text = f"     •   {clean_title}   •     "
    r_center.font.name = FONT_FAMILY
    r_center.font.size = Pt(9)
    r_center.font.color.rgb = COLOR_MUTED

    r_right = p_foot.add_run()
    r_right.text = f"Slide {index:02d} / {total_slides:02d}"
    r_right.font.name = FONT_FAMILY
    r_right.font.size = Pt(9)
    r_right.font.bold = True
    r_right.font.color.rgb = COLOR_NAVY


def _render_hero_title_slide(slide, data: Dict, total_slides: int, paper_title: str):
    # Top bar
    accent = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0), Inches(0), Inches(13.333), Inches(0.18)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_INDIGO
    accent.line.fill.background()

    # Badge Pill
    badge = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(0.9), Inches(0.7), Inches(5.8), Inches(0.42)
    )
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_BADGE_BG
    badge.line.color.rgb = COLOR_BORDER_ACCENT
    badge.line.width = Pt(1)
    b_tf = badge.text_frame
    b_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_b = b_tf.paragraphs[0]
    p_b.alignment = PP_ALIGN.CENTER
    r_b = p_b.add_run()
    r_b.text = "RESEARCHX • FINAL-YEAR PROJECT DEFENSE & VIVA"
    r_b.font.name = FONT_FAMILY
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_b.font.color.rgb = COLOR_INDIGO

    # Main Title
    title_box = slide.shapes.add_textbox(Inches(0.9), Inches(1.3), Inches(11.533), Inches(1.5))
    title_tf = title_box.text_frame
    title_tf.word_wrap = True
    title_tf.margin_left = title_tf.margin_right = title_tf.margin_top = title_tf.margin_bottom = 0
    p_title = title_tf.paragraphs[0]
    p_title.text = data["title"]
    p_title.font.name = FONT_FAMILY
    p_title.font.size = Pt(29)
    p_title.font.bold = True
    p_title.font.color.rgb = COLOR_NAVY

    # Subtitle
    if data["takeaway"]:
        clean_sub = re.sub(r"^(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway):\s*", "", data["takeaway"], flags=re.IGNORECASE).strip()
        if clean_sub:
            sub_box = slide.shapes.add_textbox(Inches(0.9), Inches(2.95), Inches(11.533), Inches(0.5))
            sub_tf = sub_box.text_frame
            sub_tf.word_wrap = True
            sub_tf.margin_left = sub_tf.margin_right = sub_tf.margin_top = sub_tf.margin_bottom = 0
            p_sub = sub_tf.paragraphs[0]
            p_sub.text = clean_sub
            p_sub.font.name = FONT_FAMILY
            p_sub.font.size = Pt(13)
            p_sub.font.italic = True
            p_sub.font.color.rgb = COLOR_MUTED

    # 2 Structured Identity & Scope Cards (Zero Truncation)
    bullets = data.get("bullets", [])
    midpoint = max(1, (len(bullets) + 1) // 2)
    left_bullets = bullets[:midpoint]
    right_bullets = bullets[midpoint:]

    meta_cards_spec = [
        (Inches(0.9), Inches(5.6), "RESEARCH IDENTITY & INVESTIGATORS", left_bullets, COLOR_INDIGO),
        (Inches(6.833), Inches(5.6), "TARGET VENUE & CORE THEME", right_bullets, COLOR_COBALT),
    ]

    for left_pos, width_val, card_title, card_bullets_list, accent_color in meta_cards_spec:
        card = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            left_pos, Inches(3.55), width_val, Inches(3.05)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)

        # Header bar on card
        card_header = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            left_pos, Inches(3.55), width_val, Inches(0.42)
        )
        card_header.fill.solid()
        card_header.fill.fore_color.rgb = COLOR_BADGE_BG
        card_header.line.color.rgb = COLOR_BORDER
        card_header.line.width = Pt(0.75)
        h_tf = card_header.text_frame
        h_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_h = h_tf.paragraphs[0]
        p_h.alignment = PP_ALIGN.LEFT
        p_h.margin_left = Inches(0.2)
        r_h = p_h.add_run()
        r_h.text = card_title
        r_h.font.name = FONT_FAMILY
        r_h.font.size = Pt(10)
        r_h.font.bold = True
        r_h.font.color.rgb = accent_color

        # Content text
        content_box = slide.shapes.add_textbox(
            left_pos + Inches(0.25), Inches(4.1), width_val - Inches(0.5), Inches(2.35)
        )
        c_tf = content_box.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0

        for b_idx, bullet in enumerate(card_bullets_list):
            lead, body = _split_lead_in(bullet)
            p = c_tf.paragraphs[0] if b_idx == 0 else c_tf.add_paragraph()
            _add_paragraph_runs(p, lead, body, bullet_color=accent_color, font_size=Pt(12.5))

    # Bottom footer
    divider = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0.9), Inches(6.82), Inches(11.533), Pt(0.75)
    )
    divider.fill.solid()
    divider.fill.fore_color.rgb = COLOR_BORDER
    divider.line.fill.background()

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.92), Inches(11.533), Inches(0.35))
    foot_tf = foot_box.text_frame
    foot_tf.word_wrap = True
    foot_tf.margin_left = foot_tf.margin_right = foot_tf.margin_top = foot_tf.margin_bottom = 0
    p_foot = foot_tf.paragraphs[0]

    r_left = p_foot.add_run()
    r_left.text = "ResearchX Academic Automation Platform  |  College Final-Year Project Presentation"
    r_left.font.name = FONT_FAMILY
    r_left.font.size = Pt(9)
    r_left.font.color.rgb = COLOR_MUTED

    r_right = p_foot.add_run()
    r_right.text = f"             •             Slide 01 / {total_slides:02d}"
    r_right.font.name = FONT_FAMILY
    r_right.font.size = Pt(9)
    r_right.font.bold = True
    r_right.font.color.rgb = COLOR_NAVY


def _render_two_column_split_slide(
    slide, data: Dict, index: int, total_slides: int, paper_title: str,
    left_header: str = "TECHNICAL CHALLENGES & SCOPE",
    right_header: str = "PROPOSED OBJECTIVES & DELIVERABLES"
):
    _setup_slide_base(slide, data["category"], data["title"], data["takeaway"], index, total_slides, paper_title)

    bullets = data["bullets"]
    midpoint = max(1, (len(bullets) + 1) // 2)
    left_bullets = bullets[:midpoint]
    right_bullets = bullets[midpoint:]

    columns_spec = [
        (Inches(0.9), Inches(5.6), left_header, left_bullets, COLOR_INDIGO),
        (Inches(6.833), Inches(5.6), right_header, right_bullets, COLOR_COBALT),
    ]

    for left_pos, width_val, col_header, col_bullets, accent_color in columns_spec:
        card = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            left_pos, Inches(1.88), width_val, Inches(4.75)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)

        header_bar = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            left_pos, Inches(1.88), width_val, Inches(0.48)
        )
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = COLOR_BADGE_BG
        header_bar.line.color.rgb = COLOR_BORDER
        header_bar.line.width = Pt(0.75)

        h_tf = header_bar.text_frame
        h_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_h = h_tf.paragraphs[0]
        p_h.margin_left = Inches(0.2)
        r_h = p_h.add_run()
        r_h.text = col_header
        r_h.font.name = FONT_FAMILY
        r_h.font.size = Pt(11)
        r_h.font.bold = True
        r_h.font.color.rgb = accent_color

        content_box = slide.shapes.add_textbox(
            left_pos + Inches(0.3), Inches(2.5), width_val - Inches(0.6), Inches(3.95)
        )
        c_tf = content_box.text_frame
        c_tf.word_wrap = True
        c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0

        for b_idx, bullet in enumerate(col_bullets):
            lead, body = _split_lead_in(bullet)
            p = c_tf.paragraphs[0] if b_idx == 0 else c_tf.add_paragraph()
            _add_paragraph_runs(p, lead, body, bullet_color=accent_color, font_size=Pt(13.5))


def _render_process_flow_slide(slide, data: Dict, index: int, total_slides: int, paper_title: str):
    _setup_slide_base(slide, data["category"], data["title"], data["takeaway"], index, total_slides, paper_title)

    bullets = data["bullets"]
    # 4 Steps horizontally
    step_width = Inches(2.5)
    arrow_width = Inches(0.38)
    start_left = Inches(0.9)
    top_pos = Inches(1.88)
    step_height = Inches(2.25)

    step_colors = [COLOR_INDIGO, COLOR_COBALT, COLOR_VIOLET, COLOR_COBALT]

    for i in range(4):
        x = start_left + i * (step_width + arrow_width + Inches(0.08))

        card = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            x, top_pos, step_width, step_height
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)

        # Step Badge
        pill = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            x + Inches(0.15), top_pos + Inches(0.15), Inches(0.85), Inches(0.32)
        )
        pill.fill.solid()
        pill.fill.fore_color.rgb = COLOR_BADGE_BG
        pill.line.fill.background()
        p_pill = pill.text_frame.paragraphs[0]
        p_pill.alignment = PP_ALIGN.CENTER
        r_pill = p_pill.add_run()
        r_pill.text = f"STAGE {i + 1}"
        r_pill.font.name = FONT_FAMILY
        r_pill.font.size = Pt(8.5)
        r_pill.font.bold = True
        r_pill.font.color.rgb = step_colors[i]

        # Step Text
        bullet_item = bullets[i] if i < len(bullets) else f"Step {i+1}: Theoretical & empirical verification component"
        lead, body = _split_lead_in(bullet_item)
        if not lead:
            lead = f"Phase {i+1}:"

        box = slide.shapes.add_textbox(x + Inches(0.15), top_pos + Inches(0.55), step_width - Inches(0.3), Inches(1.55))
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.space_after = Pt(4)
        r1 = p1.add_run()
        r1.text = lead.replace(":", "")
        r1.font.name = FONT_FAMILY
        r1.font.size = Pt(12.5)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_NAVY

        p2 = tf.add_paragraph()
        p2.line_spacing = 1.15
        r2 = p2.add_run()
        r2.text = body[:120] + ("..." if len(body) > 120 else "")
        r2.font.name = FONT_FAMILY
        r2.font.size = Pt(11)
        r2.font.color.rgb = COLOR_BODY

        # Directional connecting arrow to next step
        if i < 3:
            arrow_x = x + step_width + Inches(0.04)
            arrow = slide.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.RIGHT_ARROW,
                arrow_x, top_pos + Inches(0.95), arrow_width, Inches(0.32)
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = COLOR_INDIGO
            arrow.line.fill.background()

    # Lower Architecture Highlights Card
    low_card = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(0.9), Inches(4.35), Inches(11.533), Inches(2.28)
    )
    low_card.fill.solid()
    low_card.fill.fore_color.rgb = COLOR_CARD_BG
    low_card.line.color.rgb = COLOR_BORDER
    low_card.line.width = Pt(1)

    h_bar = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0.9), Inches(4.35), Inches(11.533), Inches(0.42)
    )
    h_bar.fill.solid()
    h_bar.fill.fore_color.rgb = COLOR_BADGE_BG
    h_bar.line.color.rgb = COLOR_BORDER
    h_bar.line.width = Pt(0.75)
    p_hb = h_bar.text_frame.paragraphs[0]
    p_hb.margin_left = Inches(0.2)
    r_hb = p_hb.add_run()
    r_hb.text = "SYSTEM PIPELINE & MATHEMATICAL HIGHLIGHTS"
    r_hb.font.name = FONT_FAMILY
    r_hb.font.size = Pt(10.5)
    r_hb.font.bold = True
    r_hb.font.color.rgb = COLOR_INDIGO

    # Split remaining or all bullets across 2 columns
    box_l = slide.shapes.add_textbox(Inches(1.2), Inches(4.9), Inches(5.3), Inches(1.6))
    tf_l = box_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0

    box_r = slide.shapes.add_textbox(Inches(6.8), Inches(4.9), Inches(5.3), Inches(1.6))
    tf_r = box_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

    half = max(1, (len(bullets) + 1) // 2)
    for b_idx, b in enumerate(bullets[:half]):
        lead, body = _split_lead_in(b)
        p = tf_l.paragraphs[0] if b_idx == 0 else tf_l.add_paragraph()
        _add_paragraph_runs(p, lead, body, bullet_color=COLOR_INDIGO, font_size=Pt(12.5))

    for b_idx, b in enumerate(bullets[half:4]):
        lead, body = _split_lead_in(b)
        p = tf_r.paragraphs[0] if b_idx == 0 else tf_r.add_paragraph()
        _add_paragraph_runs(p, lead, body, bullet_color=COLOR_COBALT, font_size=Pt(12.5))


def _render_multi_card_grid_slide(slide, data: Dict, index: int, total_slides: int, paper_title: str):
    _setup_slide_base(slide, data["category"], data["title"], data["takeaway"], index, total_slides, paper_title)

    bullets = data["bullets"]
    grid_coords = [
        (Inches(0.9), Inches(1.88), Inches(5.6), Inches(2.3)),
        (Inches(6.833), Inches(1.88), Inches(5.6), Inches(2.3)),
        (Inches(0.9), Inches(4.35), Inches(5.6), Inches(2.3)),
        (Inches(6.833), Inches(4.35), Inches(5.6), Inches(2.3)),
    ]

    card_colors = [COLOR_INDIGO, COLOR_COBALT, COLOR_VIOLET, COLOR_INDIGO]

    for i in range(4):
        left, top, width, height = grid_coords[i]
        bullet_item = bullets[i] if i < len(bullets) else f"Specification {i+1}: Verified academic parameter."
        lead, body = _split_lead_in(bullet_item)

        card = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            left, top, width, height
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)

        # Top Accent Pill / Header
        h_pill = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            left + Inches(0.2), top + Inches(0.18), Inches(2.2), Inches(0.32)
        )
        h_pill.fill.solid()
        h_pill.fill.fore_color.rgb = COLOR_BADGE_BG
        h_pill.line.color.rgb = COLOR_BORDER
        h_pill.line.width = Pt(0.75)
        p_hp = h_pill.text_frame.paragraphs[0]
        p_hp.alignment = PP_ALIGN.CENTER
        r_hp = p_hp.add_run()
        clean_lead = lead.replace(":", "").strip() if lead else f"COMPONENT {i+1}"
        r_hp.text = clean_lead[:22]
        r_hp.font.name = FONT_FAMILY
        r_hp.font.size = Pt(9)
        r_hp.font.bold = True
        r_hp.font.color.rgb = card_colors[i]

        # Text Box
        t_box = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.62), width - Inches(0.5), height - Inches(0.75))
        tf = t_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p = tf.paragraphs[0]
        p.line_spacing = 1.2
        r_b = p.add_run()
        r_b.text = body if body else bullet_item
        r_b.font.name = FONT_FAMILY
        r_b.font.size = Pt(13)
        r_b.font.color.rgb = COLOR_BODY


def _render_results_metrics_slide(slide, data: Dict, index: int, total_slides: int, paper_title: str):
    _setup_slide_base(slide, data["category"], data["title"], data["takeaway"], index, total_slides, paper_title)

    bullets = data["bullets"]

    # 1. Top Section: 3 Metric Highlight Badges
    metric_specs = [
        (Inches(0.9), Inches(3.6), "PRIMARY SOTA GAIN", "+14.8% Gain", COLOR_COBALT),
        (Inches(4.85), Inches(3.75), "BASELINE OUTPERFORMANCE", "State-of-the-Art", COLOR_INDIGO),
        (Inches(8.9), Inches(3.53), "EFFICIENCY & SCALABILITY", "Sub-Second Latency", COLOR_SUCCESS),
    ]

    for idx, (left, width, title, fallback_val, color) in enumerate(metric_specs):
        card = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            left, Inches(1.88), width, Inches(1.42)
        )
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1)

        t_box = slide.shapes.add_textbox(left + Inches(0.2), Inches(1.98), width - Inches(0.4), Inches(1.2))
        tf = t_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        r1 = p1.add_run()
        r1.text = title
        r1.font.name = FONT_FAMILY
        r1.font.size = Pt(9)
        r1.font.bold = True
        r1.font.color.rgb = COLOR_MUTED

        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        bullet_item = bullets[idx] if idx < len(bullets) else fallback_val
        lead, body = _split_lead_in(bullet_item)
        val_display = (lead.replace(":", "") if lead else fallback_val)[:22]
        r2.text = val_display
        r2.font.name = FONT_FAMILY
        r2.font.size = Pt(17)
        r2.font.bold = True
        r2.font.color.rgb = color

        p3 = tf.add_paragraph()
        r3 = p3.add_run()
        r3.text = (body if body else bullet_item)[:65] + "..."
        r3.font.name = FONT_FAMILY
        r3.font.size = Pt(10)
        r3.font.color.rgb = COLOR_BODY

    # 2. Bottom Section: Native PowerPoint Comparison Table
    table_shape = slide.shapes.add_table(
        rows=5, cols=4,
        left=Inches(0.9), top=Inches(3.48), width=Inches(11.533), height=Inches(3.15)
    )
    tbl = table_shape.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(2.6)
    tbl.columns[2].width = Inches(2.8)
    tbl.columns[3].width = Inches(2.933)

    headers = ["Evaluation Dimension / Task", "Baseline Competitor", "Proposed Architecture", "Empirical Margin / Significance"]
    for col_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_COBALT
        cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.12)
        cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.08)
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = h_text
        r.font.name = FONT_FAMILY
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = COLOR_WHITE

    # Populate rows with bullet data
    for r_idx in range(1, 5):
        b_index = r_idx - 1
        bullet_item = bullets[b_index] if b_index < len(bullets) else f"Evaluation metric {r_idx}: robust benchmark"
        lead, body = _split_lead_in(bullet_item)

        dim_text = lead.replace(":", "") if lead else f"Metric {r_idx}"
        base_text = "Prior Published SOTA"
        prop_text = "Proposed Framework"
        margin_text = body[:60] if body else "Statistically verified improvement"

        row_data = [dim_text, base_text, prop_text, margin_text]
        row_bg = COLOR_WHITE if r_idx % 2 == 1 else COLOR_CARD_ALT

        for c_idx, val in enumerate(row_data):
            cell = tbl.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = row_bg
            cell.text_frame.margin_left = cell.text_frame.margin_right = Inches(0.12)
            cell.text_frame.margin_top = cell.text_frame.margin_bottom = Inches(0.08)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = val
            r.font.name = FONT_FAMILY
            r.font.size = Pt(10)
            if c_idx == 2:
                r.font.bold = True
                r.font.color.rgb = COLOR_NAVY
            elif c_idx == 3:
                r.font.color.rgb = COLOR_INDIGO
                r.font.bold = True
            else:
                r.font.color.rgb = COLOR_BODY


def _render_gap_analysis_slide(slide, data: Dict, index: int, total_slides: int, paper_title: str):
    _setup_slide_base(slide, data["category"], data["title"], data["takeaway"], index, total_slides, paper_title)

    bullets = data["bullets"]
    half = max(1, len(bullets) // 2)
    prior_bullets = bullets[:half]
    limit_bullets = bullets[half:-1] if len(bullets) > 2 else bullets[half:]
    gap_bullet = bullets[-1] if len(bullets) >= 3 else "Identified Gap: Need for robust unified architecture."

    # 1. Left Card: Prior Works
    card_l = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(1.88), Inches(5.6), Inches(2.45))
    card_l.fill.solid()
    card_l.fill.fore_color.rgb = COLOR_CARD_BG
    card_l.line.color.rgb = COLOR_BORDER
    card_l.line.width = Pt(1)

    h_l = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.9), Inches(1.88), Inches(5.6), Inches(0.42))
    h_l.fill.solid()
    h_l.fill.fore_color.rgb = COLOR_BADGE_BG
    h_l.line.fill.background()
    p_hl = h_l.text_frame.paragraphs[0]
    p_hl.margin_left = Inches(0.2)
    r_hl = p_hl.add_run()
    r_hl.text = "PRIOR APPROACHES & STATE-OF-THE-ART"
    r_hl.font.name = FONT_FAMILY
    r_hl.font.size = Pt(10.5)
    r_hl.font.bold = True
    r_hl.font.color.rgb = COLOR_INDIGO

    tb_l = slide.shapes.add_textbox(Inches(1.15), Inches(2.42), Inches(5.1), Inches(1.75))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0
    for b_idx, b in enumerate(prior_bullets):
        lead, body = _split_lead_in(b)
        p = tf_l.paragraphs[0] if b_idx == 0 else tf_l.add_paragraph()
        _add_paragraph_runs(p, lead, body, bullet_color=COLOR_INDIGO, font_size=Pt(12.5))

    # 2. Right Card: Inherent Limitations
    card_r = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(6.833), Inches(1.88), Inches(5.6), Inches(2.45))
    card_r.fill.solid()
    card_r.fill.fore_color.rgb = COLOR_CARD_BG
    card_r.line.color.rgb = COLOR_BORDER
    card_r.line.width = Pt(1)

    h_r = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(6.833), Inches(1.88), Inches(5.6), Inches(0.42))
    h_r.fill.solid()
    h_r.fill.fore_color.rgb = COLOR_BADGE_BG
    h_r.line.fill.background()
    p_hr = h_r.text_frame.paragraphs[0]
    p_hr.margin_left = Inches(0.2)
    r_hr = p_hr.add_run()
    r_hr.text = "INHERENT CONSTRAINTS & OVERHEADS"
    r_hr.font.name = FONT_FAMILY
    r_hr.font.size = Pt(10.5)
    r_hr.font.bold = True
    r_hr.font.color.rgb = COLOR_AMBER

    tb_r = slide.shapes.add_textbox(Inches(7.1), Inches(2.42), Inches(5.1), Inches(1.75))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0
    for b_idx, b in enumerate(limit_bullets):
        lead, body = _split_lead_in(b)
        p = tf_r.paragraphs[0] if b_idx == 0 else tf_r.add_paragraph()
        _add_paragraph_runs(p, lead, body, bullet_color=COLOR_AMBER, font_size=Pt(12.5))

    # 3. Bottom Card: Highlighted Research Gap
    gap_card = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(4.5), Inches(11.533), Inches(2.15))
    gap_card.fill.solid()
    gap_card.fill.fore_color.rgb = COLOR_BADGE_BG
    gap_card.line.color.rgb = COLOR_INDIGO
    gap_card.line.width = Pt(1.5)

    g_box = slide.shapes.add_textbox(Inches(1.2), Inches(4.65), Inches(11.0), Inches(1.8))
    g_tf = g_box.text_frame
    g_tf.word_wrap = True
    g_tf.margin_left = g_tf.margin_right = g_tf.margin_top = g_tf.margin_bottom = 0

    p_gh = g_tf.paragraphs[0]
    p_gh.space_after = Pt(6)
    r_gh = p_gh.add_run()
    r_gh.text = "★  CRITICAL RESEARCH GAP BRIDGED BY THIS WORK"
    r_gh.font.name = FONT_FAMILY
    r_gh.font.size = Pt(11.5)
    r_gh.font.bold = True
    r_gh.font.color.rgb = COLOR_INDIGO

    p_gb = g_tf.add_paragraph()
    p_gb.line_spacing = 1.25
    g_lead, g_body = _split_lead_in(gap_bullet)
    if g_lead:
        r_gl = p_gb.add_run()
        r_gl.text = g_lead
        r_gl.font.name = FONT_FAMILY
        r_gl.font.size = Pt(14)
        r_gl.font.bold = True
        r_gl.font.color.rgb = COLOR_NAVY
    r_gt = p_gb.add_run()
    r_gt.text = g_body
    r_gt.font.name = FONT_FAMILY
    r_gt.font.size = Pt(14)
    r_gt.font.color.rgb = COLOR_BODY


def _render_closing_qa_slide(slide, total_slides: int, paper_title: str):
    accent = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.RECTANGLE,
        Inches(0), Inches(0), Inches(13.333), Inches(0.18)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_INDIGO
    accent.line.fill.background()

    card = slide.shapes.add_shape(
        MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
        Inches(1.666), Inches(1.25), Inches(10.0), Inches(5.1)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = COLOR_BORDER_ACCENT
    card.line.width = Pt(1.5)

    box = slide.shapes.add_textbox(Inches(2.1), Inches(1.8), Inches(9.133), Inches(4.0))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p_badge = tf.paragraphs[0]
    p_badge.alignment = PP_ALIGN.CENTER
    p_badge.space_after = Pt(14)
    r_badge = p_badge.add_run()
    r_badge.text = "PROJECT DEFENSE & VIVA VOCE CONCLUDED"
    r_badge.font.name = FONT_FAMILY
    r_badge.font.size = Pt(11)
    r_badge.font.bold = True
    r_badge.font.color.rgb = COLOR_INDIGO

    p_title = tf.add_paragraph()
    p_title.alignment = PP_ALIGN.CENTER
    p_title.space_after = Pt(8)
    r_title = p_title.add_run()
    r_title.text = "Thank You!"
    r_title.font.name = FONT_FAMILY
    r_title.font.size = Pt(38)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = tf.add_paragraph()
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.space_after = Pt(24)
    r_sub = p_sub.add_run()
    r_sub.text = "Open for Questions, Evaluation & Faculty Viva Discussion"
    r_sub.font.name = FONT_FAMILY
    r_sub.font.size = Pt(16)
    r_sub.font.bold = True
    r_sub.font.color.rgb = COLOR_COBALT

    p_doc = tf.add_paragraph()
    p_doc.alignment = PP_ALIGN.CENTER
    p_doc.line_spacing = 1.25
    r_doc = p_doc.add_run()
    clean_title = (paper_title or "Research Presentation").replace(".pdf", "")
    r_doc.text = f"Project: {clean_title}\nResearchX Academic Automation Platform  |  Academic Year 2026"
    r_doc.font.name = FONT_FAMILY
    r_doc.font.size = Pt(12)
    r_doc.font.color.rgb = COLOR_MUTED


def _get_academic_headers_for_slide(category: str, title: str) -> Tuple[str, str]:
    cat = category.upper()
    tit = title.upper()
    if any(k in cat or k in tit for k in ["MOTIVATION", "URGENCY", "CONTEXT"]):
        return ("SCIENTIFIC CHALLENGES & MOTIVATION", "INDUSTRY URGENCY & RESEARCH OPPORTUNITY")
    elif any(k in cat or k in tit for k in ["PROBLEM", "OBJECTIVE", "GOAL", "AIM"]):
        return ("PROBLEM FORMULATION & SCOPE", "CORE RESEARCH OBJECTIVES & DELIVERABLES")
    elif any(k in cat or k in tit for k in ["LITERATURE", "RELATED WORK", "PRIOR", "LANDSCAPE", "GAP"]):
        return ("STATE-OF-THE-ART & PRIOR APPROACHES", "CRITICAL BOTTLENECKS & BRIDGED GAP")
    elif any(k in cat or k in tit for k in ["ARCHITECTURE", "SYSTEM", "FRAMEWORK", "THEORETICAL"]):
        return ("THEORETICAL FRAMEWORK & CORE MODULES", "DATA FLOW & ARCHITECTURAL MECHANICS")
    elif any(k in cat or k in tit for k in ["IMPLEMENTATION", "ALGORITHMIC", "PIPELINE", "TECHNICAL"]):
        return ("ALGORITHMIC MECHANICS & FORMULATION", "SYSTEM PIPELINE & COMPUTATIONAL PROTOCOLS")
    elif any(k in cat or k in tit for k in ["DATASET", "SETUP", "EXPERIMENT", "BENCHMARK SETUP"]):
        return ("BENCHMARK DATASETS & HARDWARE SETUP", "COMPARATIVE BASELINES & EVALUATION METRICS")
    elif any(k in cat or k in tit for k in ["RESULT", "EMPIRICAL", "PERFORMANCE", "SCORE"]):
        return ("PRIMARY BENCHMARK FINDINGS & GAINS", "COMPARATIVE ANALYSIS & SOTA PERFORMANCE")
    elif any(k in cat or k in tit for k in ["EVALUATION", "ABLATION", "INSIGHT"]):
        return ("ABLATION STUDIES & HYPERPARAMETER IMPACT", "EMPIRICAL RIGOR & QUALITATIVE EVALUATION")
    elif any(k in cat or k in tit for k in ["CONTRIBUTION", "INNOVATION", "ADVANTAGE"]):
        return ("NOVEL TECHNICAL CONTRIBUTIONS", "METHODOLOGICAL ADVANTAGES & SIGNIFICANCE")
    elif any(k in cat or k in tit for k in ["LIMITATION", "FUTURE", "CONCLUSION", "ROADMAP"]):
        return ("SYNTHESIS OF EMPIRICAL FINDINGS", "LIMITATIONS & FUTURE RESEARCH DIRECTIONS")
    else:
        return ("RESEARCH FORMULATION & METHODOLOGY", "EMPIRICAL FINDINGS & SCIENTIFIC TAKEAWAYS")


def create_ppt(
    presentation_text: str,
    output_path: str,
    paper_title: Optional[str] = None,
) -> str:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slides_data = _parse_raw_presentation(presentation_text)
    if not slides_data:
        slides_data = [{
            "title": paper_title or "Research Presentation",
            "category": "EXECUTIVE SUMMARY",
            "takeaway": "Presentation synthesized from uploaded research artifact.",
            "bullets": [presentation_text[:300]],
            "speaker_notes": "Welcome to the presentation."
        }]

    # Filter out any standalone 'Key Insights' / 'Key Takeaways' slides
    # and merge their important information into the appropriate academic slides
    slides_data = _filter_and_merge_insight_slides(slides_data)
    _sanitize_slide_titles_and_subtitles(slides_data)

    # Single Source of Truth: Total slides must exactly match UI preview slide count
    total_slides = len(slides_data)
    blank_layout = prs.slide_layouts[6]

    for index, data in enumerate(slides_data, start=1):
        slide = prs.slides.add_slide(blank_layout)
        cat_upper = data["category"].upper()
        title_upper = data["title"].upper()

        if index == 1:
            _render_hero_title_slide(slide, data, total_slides, paper_title or data["title"])
        else:
            left_header, right_header = _get_academic_headers_for_slide(cat_upper, title_upper)
            _render_two_column_split_slide(
                slide,
                data,
                index,
                total_slides,
                paper_title or data["title"],
                left_header=left_header,
                right_header=right_header,
            )

        if data.get("speaker_notes"):
            notes_slide = slide.notes_slide
            notes_tf = notes_slide.notes_text_frame
            notes_tf.text = data["speaker_notes"]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    prs.save(output_path)
    return output_path

