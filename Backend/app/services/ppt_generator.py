import os
import re
from typing import Dict, List, Tuple

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

COLOR_NAVY = RGBColor(15, 23, 42)          # #0F172A - Deep Slate Navy
COLOR_INDIGO = RGBColor(79, 70, 229)       # #4F46E5 - ResearchX Primary Indigo
COLOR_COBALT = RGBColor(37, 99, 235)       # #2563EB - IEEE Cobalt Blue
COLOR_BODY = RGBColor(51, 65, 85)          # #334155 - High Contrast Body Text
COLOR_MUTED = RGBColor(100, 116, 139)      # #64748B - Subtitles & Footers
COLOR_CARD_BG = RGBColor(255, 255, 255)    # #FFFFFF - Clean Solid Card Surface
COLOR_BORDER = RGBColor(226, 232, 240)     # #E2E8F0 - Subtle 1pt Border
COLOR_BORDER_ACCENT = RGBColor(199, 210, 254) # #C7D2FE
COLOR_BADGE_BG = RGBColor(238, 242, 255)   # #EEF2FF
COLOR_WHITE = RGBColor(255, 255, 255)

FONT_FAMILY = "Calibri"


def _split_lead(text: str):
    match = re.match(r"^\*\*(.*?)\*\*:?\s*(.*)", text)
    if match:
        lead = match.group(1).strip()
        body = match.group(2).strip()
        lead = re.sub(r"^(?:Key\s+Insights?|Insight)\b", "Core Finding", lead, flags=re.IGNORECASE).strip()
        lead = re.sub(r"^(?:Key\s+Takeaways?|Takeaway)\b", "Empirical Deliverable", lead, flags=re.IGNORECASE).strip()
        if not lead.endswith(":"):
            lead += ":"
        return f"{lead} ", body
    if ":" in text:
        parts = text.split(":", 1)
        if len(parts[0].split()) <= 4:
            clean_first = parts[0].strip()
            clean_first = re.sub(r"^(?:Key\s+Insights?|Insight)\b", "Core Finding", clean_first, flags=re.IGNORECASE).strip()
            clean_first = re.sub(r"^(?:Key\s+Takeaways?|Takeaway)\b", "Empirical Deliverable", clean_first, flags=re.IGNORECASE).strip()
            return f"{clean_first}: ", parts[1].strip()
    return "", text


def _trim_bullet_text(bullet: str, max_words: int = 26) -> str:
    """Ensure bullet points stay crisp and do not crowd the slide."""
    lead, body = _split_lead(bullet)
    words = body.split()
    if len(words) > max_words:
        body = " ".join(words[:max_words]).rstrip(",;:-.") + "..."
    if lead:
        return f"{lead}{body}"
    return body


def _calculate_adaptive_typography(
    bullets: List[str],
    max_available_height_inches: float = 4.0,
) -> Tuple[Pt, Pt, float]:
    """Dynamically determine font size, space_after, and line spacing."""
    count = len(bullets)
    total_chars = sum(len(b) for b in bullets)

    if count <= 1:
        if total_chars < 140:
            return Pt(16.5), Pt(18), 1.35
        elif total_chars < 220:
            return Pt(15.0), Pt(14), 1.30
        else:
            return Pt(13.5), Pt(10), 1.22
    elif count == 2:
        if total_chars < 200:
            return Pt(15.5), Pt(18), 1.32
        elif total_chars < 320:
            return Pt(14.0), Pt(14), 1.25
        else:
            return Pt(12.5), Pt(10), 1.20
    elif count == 3:
        if total_chars < 300:
            return Pt(13.5), Pt(12), 1.22
        elif total_chars < 420:
            return Pt(12.5), Pt(8), 1.18
        else:
            return Pt(11.5), Pt(5), 1.14
    elif count == 4:
        if total_chars < 420:
            return Pt(12.0), Pt(7), 1.16
        else:
            return Pt(11.0), Pt(5), 1.12
    else:
        if total_chars < 500:
            return Pt(11.0), Pt(4), 1.12
        else:
            return Pt(10.0), Pt(3), 1.08



def generate_ieee_presentation(paper_title: str, slides_content: List[Dict]) -> str:
    # Filter and merge any standalone Key Insights / Takeaways slides
    filtered_content = []
    insight_slides = []
    for s in slides_content:
        h = s.get("heading", "").lower()
        if any(k in h for k in ["key insight", "key takeaway", "insights", "takeaways"]):
            insight_slides.append(s)
        else:
            filtered_content.append(s)

    if insight_slides and filtered_content:
        for islide in insight_slides:
            for pt in islide.get("points", []):
                pt_clean = re.sub(r"^(?:\*\*)?(?:Key\s+Insights?|Key\s+Takeaways?|Insight|Takeaway)(?:\*\*)?:?\s*", "", pt, flags=re.I).strip()
                target = filtered_content[-1]
                for fc in filtered_content:
                    fch = fc.get("heading", "").lower()
                    if "result" in fch or "gap" in fch or "conclusion" in fch:
                        target = fc
                        break
                if pt_clean not in target.get("points", []):
                    target.setdefault("points", []).append(f"**Empirical Finding:** {pt_clean}")
        slides_content = filtered_content

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    clean_title = paper_title.replace(".pdf", "").strip()
    total_slides = len(slides_content) + 2  # Cover + Content + Closing

    # ----------------------------------------------------
    # Slide 1: Cover Slide
    # ----------------------------------------------------
    cover = prs.slides.add_slide(blank_layout)
    bar = cover.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_INDIGO
    bar.line.fill.background()

    badge = cover.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(0.8), Inches(5.6), Inches(0.42))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_BADGE_BG
    badge.line.color.rgb = COLOR_BORDER_ACCENT
    badge.line.width = Pt(1)
    p_b = badge.text_frame.paragraphs[0]
    p_b.alignment = PP_ALIGN.CENTER
    r_b = p_b.add_run()
    r_b.text = "RESEARCHX • IEEE ACADEMIC PRESENTATION & DEFENSE"
    r_b.font.name = FONT_FAMILY
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_b.font.color.rgb = COLOR_INDIGO

    t_box = cover.shapes.add_textbox(Inches(0.9), Inches(1.45), Inches(11.533), Inches(1.6))
    t_tf = t_box.text_frame
    t_tf.word_wrap = True
    t_p = t_tf.paragraphs[0]
    t_p.text = clean_title
    t_p.font.name = FONT_FAMILY
    if len(clean_title) > 75:
        t_p.font.size = Pt(21)
    elif len(clean_title) > 45:
        t_p.font.size = Pt(24.5)
    else:
        t_p.font.size = Pt(28)
    t_p.font.bold = True
    t_p.font.color.rgb = COLOR_NAVY

    sub_box = cover.shapes.add_textbox(Inches(0.9), Inches(3.1), Inches(11.533), Inches(0.45))
    s_tf = sub_box.text_frame
    s_p = s_tf.paragraphs[0]
    s_p.text = "Automated Research Synthesis, Critical Analysis & Technical Defense Deck"
    s_p.font.name = FONT_FAMILY
    s_p.font.size = Pt(13)
    s_p.font.italic = True
    s_p.font.color.rgb = COLOR_MUTED

    card = cover.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(3.75), Inches(11.533), Inches(2.7))
    card.fill.solid()
    card.fill.fore_color.rgb = COLOR_CARD_BG
    card.line.color.rgb = COLOR_BORDER
    card.line.width = Pt(1)

    c_tf = card.text_frame
    c_tf.word_wrap = True
    c_tf.vertical_anchor = MSO_ANCHOR.TOP
    c_tf.margin_left = c_tf.margin_right = Inches(0.4)
    c_tf.margin_top = c_tf.margin_bottom = Inches(0.35)

    meta_items = [
        ("Domain:", "IEEE Academic Research Automation & Analysis"),
        ("Source Document:", clean_title),
        ("Evaluation Format:", "College Final-Year Project Defense / Conference Presentation Standard"),
        ("Platform:", "ResearchX Multi-Agent System")
    ]
    for m_idx, (m_lead, m_val) in enumerate(meta_items):
        p = c_tf.paragraphs[0] if m_idx == 0 else c_tf.add_paragraph()
        p.space_after = Pt(10)
        p.line_spacing = 1.2
        r1 = p.add_run()
        r1.text = "•  "
        r1.font.bold = True
        r1.font.color.rgb = COLOR_INDIGO
        r2 = p.add_run()
        r2.text = f"{m_lead} "
        r2.font.bold = True
        r2.font.color.rgb = COLOR_NAVY
        r3 = p.add_run()
        r3.text = m_val
        r3.font.color.rgb = COLOR_BODY

    foot = cover.shapes.add_textbox(Inches(0.9), Inches(6.92), Inches(11.533), Inches(0.35))
    f_p = foot.text_frame.paragraphs[0]
    r_fl = f_p.add_run()
    r_fl.text = "ResearchX Academic Automation Platform  |  IEEE Conference Standard"
    r_fl.font.size = Pt(9)
    r_fl.font.color.rgb = COLOR_MUTED
    r_fr = f_p.add_run()
    r_fr.text = f"             •             Slide 01 / {total_slides:02d}"
    r_fr.font.size = Pt(9)
    r_fr.font.bold = True
    r_fr.font.color.rgb = COLOR_NAVY

    # ----------------------------------------------------
    # Content Slides (Adaptive Typography & Auto-Fitting)
    # ----------------------------------------------------
    for s_idx, slide_data in enumerate(slides_content, start=2):
        slide = prs.slides.add_slide(blank_layout)

        bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_INDIGO
        bar.line.fill.background()

        cat_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.35), Inches(11.533), Inches(0.28))
        cp = cat_box.text_frame.paragraphs[0]
        cp.text = "TECHNICAL EVALUATION & SYNTHESIS"
        cp.font.name = FONT_FAMILY
        cp.font.size = Pt(10)
        cp.font.bold = True
        cp.font.color.rgb = COLOR_INDIGO

        h_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.65), Inches(11.533), Inches(0.68))
        hp = h_box.text_frame.paragraphs[0]
        h_text = slide_data.get("heading", f"Slide {s_idx}")
        hp.text = h_text
        hp.font.name = FONT_FAMILY
        if len(h_text) > 65:
            hp.font.size = Pt(19)
        elif len(h_text) > 42:
            hp.font.size = Pt(21)
        else:
            hp.font.size = Pt(23)
        hp.font.bold = True
        hp.font.color.rgb = COLOR_NAVY

        raw_points = slide_data.get("points", [])
        points = [_trim_bullet_text(pt, max_words=26) for pt in raw_points]
        if not points:
            points = ["Core theoretical and empirical deliverables documented in the research work."]

        if len(points) >= 4:
            # Two-column cards layout for widescreen balance
            midpoint = max(1, (len(points) + 1) // 2)
            cols = [
                (Inches(0.9), Inches(5.6), points[:midpoint], COLOR_INDIGO),
                (Inches(6.833), Inches(5.6), points[midpoint:], COLOR_COBALT),
            ]
            for c_left, c_width, c_points, c_color in cols:
                col_card = slide.shapes.add_shape(
                    MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
                    c_left, Inches(1.88), c_width, Inches(4.75)
                )
                col_card.fill.solid()
                col_card.fill.fore_color.rgb = COLOR_CARD_BG
                col_card.line.color.rgb = COLOR_BORDER
                col_card.line.width = Pt(1)

                f_sz, sp_aft, l_sp = _calculate_adaptive_typography(c_points, max_available_height_inches=4.0)
                col_box = slide.shapes.add_textbox(c_left + Inches(0.3), Inches(2.2), c_width - Inches(0.6), Inches(4.2))
                c_tf = col_box.text_frame
                c_tf.word_wrap = True
                c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0

                for p_idx, pt in enumerate(c_points):
                    lead, body = _split_lead(pt)
                    p = c_tf.paragraphs[0] if p_idx == 0 else c_tf.add_paragraph()
                    p.space_after = sp_aft
                    p.line_spacing = l_sp
                    rb = p.add_run()
                    rb.text = "•  "
                    rb.font.name = FONT_FAMILY
                    rb.font.size = f_sz
                    rb.font.bold = True
                    rb.font.color.rgb = c_color
                    if lead:
                        rl = p.add_run()
                        rl.text = lead
                        rl.font.name = FONT_FAMILY
                        rl.font.size = f_sz
                        rl.font.bold = True
                        rl.font.color.rgb = COLOR_NAVY
                    rt = p.add_run()
                    rt.text = body
                    rt.font.name = FONT_FAMILY
                    rt.font.size = f_sz
                    rt.font.color.rgb = COLOR_BODY
        else:
            # Single card with adaptive typography
            c_shape = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.9), Inches(1.88), Inches(11.533), Inches(4.75))
            c_shape.fill.solid()
            c_shape.fill.fore_color.rgb = COLOR_CARD_BG
            c_shape.line.color.rgb = COLOR_BORDER
            c_shape.line.width = Pt(1)

            f_sz, sp_aft, l_sp = _calculate_adaptive_typography(points, max_available_height_inches=4.0)
            box_top = Inches(2.5) if len(points) <= 2 else Inches(2.2)
            box_height = Inches(3.8) if len(points) <= 2 else Inches(4.2)
            c_box = slide.shapes.add_textbox(Inches(1.2), box_top, Inches(10.933), box_height)
            c_tf = c_box.text_frame
            c_tf.word_wrap = True
            c_tf.margin_left = c_tf.margin_right = c_tf.margin_top = c_tf.margin_bottom = 0

            for p_idx, pt in enumerate(points):
                lead, body = _split_lead(pt)
                p = c_tf.paragraphs[0] if p_idx == 0 else c_tf.add_paragraph()
                p.space_after = sp_aft
                p.line_spacing = l_sp

                rb = p.add_run()
                rb.text = "•  "
                rb.font.name = FONT_FAMILY
                rb.font.size = f_sz
                rb.font.bold = True
                rb.font.color.rgb = COLOR_INDIGO

                if lead:
                    rl = p.add_run()
                    rl.text = lead
                    rl.font.name = FONT_FAMILY
                    rl.font.size = f_sz
                    rl.font.bold = True
                    rl.font.color.rgb = COLOR_NAVY

                rt = p.add_run()
                rt.text = body
                rt.font.name = FONT_FAMILY
                rt.font.size = f_sz
                rt.font.color.rgb = COLOR_BODY

        div = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.9), Inches(6.82), Inches(11.533), Pt(0.75))
        div.fill.solid()
        div.fill.fore_color.rgb = COLOR_BORDER
        div.line.fill.background()

        foot = slide.shapes.add_textbox(Inches(0.9), Inches(6.92), Inches(11.533), Inches(0.35))
        fp = foot.text_frame.paragraphs[0]
        r_fl = fp.add_run()
        r_fl.text = "ResearchX Academic Automation Platform  |  College Final-Year Project Presentation"
        r_fl.font.size = Pt(9)
        r_fl.font.color.rgb = COLOR_MUTED
        r_fc = fp.add_run()
        r_fc.text = f"     •   {clean_title[:45]}   •     "
        r_fc.font.size = Pt(9)
        r_fc.font.color.rgb = COLOR_MUTED
        r_fr = fp.add_run()
        r_fr.text = f"Slide {s_idx:02d} / {total_slides:02d}"
        r_fr.font.size = Pt(9)
        r_fr.font.bold = True
        r_fr.font.color.rgb = COLOR_NAVY

    # ----------------------------------------------------
    # Slide Final: Closing Viva / Q&A Slide
    # ----------------------------------------------------
    closing = prs.slides.add_slide(blank_layout)
    bar = closing.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    bar.fill.solid()
    bar.fill.fore_color.rgb = COLOR_INDIGO
    bar.line.fill.background()

    c_card = closing.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(1.666), Inches(1.25), Inches(10.0), Inches(5.1))
    c_card.fill.solid()
    c_card.fill.fore_color.rgb = COLOR_CARD_BG
    c_card.line.color.rgb = COLOR_BORDER_ACCENT
    c_card.line.width = Pt(1.5)

    c_box = closing.shapes.add_textbox(Inches(2.1), Inches(1.8), Inches(9.133), Inches(4.0))
    ctf = c_box.text_frame
    ctf.word_wrap = True

    p_cb = ctf.paragraphs[0]
    p_cb.alignment = PP_ALIGN.CENTER
    p_cb.space_after = Pt(14)
    rcb = p_cb.add_run()
    rcb.text = "PROJECT DEFENSE & VIVA VOCE CONCLUDED"
    rcb.font.name = FONT_FAMILY
    rcb.font.size = Pt(11)
    rcb.font.bold = True
    rcb.font.color.rgb = COLOR_INDIGO

    p_ct = ctf.add_paragraph()
    p_ct.alignment = PP_ALIGN.CENTER
    p_ct.space_after = Pt(8)
    rct = p_ct.add_run()
    rct.text = "Thank You!"
    rct.font.name = FONT_FAMILY
    rct.font.size = Pt(38)
    rct.font.bold = True
    rct.font.color.rgb = COLOR_NAVY

    p_cs = ctf.add_paragraph()
    p_cs.alignment = PP_ALIGN.CENTER
    p_cs.space_after = Pt(24)
    rcs = p_cs.add_run()
    rcs.text = "Open for Questions, Evaluation & Faculty Viva Discussion"
    rcs.font.name = FONT_FAMILY
    rcs.font.size = Pt(16)
    rcs.font.bold = True
    rcs.font.color.rgb = COLOR_COBALT

    p_cd = ctf.add_paragraph()
    p_cd.alignment = PP_ALIGN.CENTER
    rcd = p_cd.add_run()
    rcd.text = f"Project: {clean_title}\nResearchX Academic Automation Platform  |  Academic Year 2026"
    rcd.font.name = FONT_FAMILY
    rcd.font.size = Pt(12)
    rcd.font.color.rgb = COLOR_MUTED

    os.makedirs("uploads/generated_ppts", exist_ok=True)
    clean_name = "".join(c for c in paper_title[:20] if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
    file_path = f"uploads/generated_ppts/{clean_name or 'paper'}.pptx"
    prs.save(file_path)
    return file_path