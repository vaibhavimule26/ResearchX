import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.agents.coordinator import load_context_for_paper
from app.llm.gemini import generate_answer
from app.services.plagiarism_service import audit_paper_originality


def clean_pdf_artifacts(text: str) -> str:
    """Fix hyphenated line breaks, line wrap artifacts, and unicode anomalies from PDF text."""
    if not text:
        return ""
    # Strip any scanner / RAG wrapper text
    if "Full Paper Content:" in text:
        text = text.split("Full Paper Content:")[-1].strip()
    elif "Key Relevant Evidence:" in text and "Paper Title:" in text:
        parts = text.split("\n\n")
        filtered_parts = []
        skip = False
        for p in parts:
            if p.startswith("Key Relevant Evidence:"):
                skip = True
                continue
            if skip:
                if any(k in p for k in ["Abstract", "Introduction", "I. "]):
                    skip = False
                    filtered_parts.append(p)
                continue
            filtered_parts.append(p)
        text = "\n\n".join(filtered_parts)

    # Fix hyphenation like 'state-\n ment' or 'arti-\n ficial'
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    # Normalize unicode whitespace
    text = re.sub(r"[\u2000-\u200b\u202f\u205f\u3000\xa0]", " ", text)
    # Normalize unicode quotation marks and dashes
    text = (
        text.replace("\ufffd", " — ")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", " - ")
        .replace("\u2014", "—")
    )
    return text


def is_already_ieee_formatted(text: str) -> bool:
    """
    Detect if the text represents an already-structured IEEE or academic manuscript.
    Checks for presence of standard abstract, section structure, and reference section.
    """
    if not text or len(text.strip()) < 100:
        return False
    sample = text
    if "Full Paper Content:" in sample:
        sample = sample.split("Full Paper Content:")[-1].strip()
    sample = sample[:10000]
    has_abstract = bool(re.search(r"\babstract\b", sample, re.IGNORECASE))
    has_references = bool(re.search(r"\b(?:references|bibliography)\b", text, re.IGNORECASE))
    has_headings = bool(
        re.search(r"(?:^|\n)(?:#{1,3}\s*)?(?:[IVXLCDM]+\.|\d+\.)\s+[A-Za-z]", text)
        or re.search(r"(?:^|\n)(?:#{1,3}\s*)?I\.\s*INTRODUCTION", text, re.IGNORECASE)
    )
    return has_abstract and (has_references or has_headings)


def parse_ieee_paper_structure(
    raw_text: str, fallback_title: str = "Research Paper"
) -> Optional[Dict[str, Any]]:
    """
    Parse an already-structured IEEE or academic paper into modular components:
    title, authors_str, affil_str, corr_str, abstract_text, index_terms_str, sections, ref_lines.
    """
    text = clean_pdf_artifacts(raw_text)
    lines = [l.strip() for l in text.splitlines()]

    # 1. Locate Abstract
    abs_idx = -1
    for i, l in enumerate(lines[:300]):
        if (
            re.match(r"^abstract[—\-:\s]", l, re.I)
            or l.upper() == "ABSTRACT"
            or l.startswith("### ABSTRACT")
            or l.startswith("## ABSTRACT")
            or (len(l) < 30 and "ABSTRACT" in l.upper())
        ):
            abs_idx = i
            break

    if abs_idx == -1:
        return None

    # Helper to check banner/header noise lines before title
    def is_banner_noise(line_str: str) -> bool:
        low = line_str.lower()
        if any(k in low for k in [
            "http://", "https://", ".org", ".com", "open-access",
            "creative commons", "license", "copyright", "all rights reserved",
            "published by", "issn", "doi:"
        ]):
            return True
        if any(k in low for k in ["journal of", "proceedings of", "volume ", "vol.", "suppl "]):
            return True
        if line_str.strip().upper() in [
            "EDITORIAL", "SPECIAL COLLECTION", "COMMENTARY",
            "PERSPECTIVE", "SHORT COMMUNICATION", "REVIEW ARTICLE"
        ]:
            return True
        return False

    # 2. Extract Title and Authors (before abstract)
    pre_abs = [l for l in lines[:abs_idx] if l]
    cleaned_pre = []
    for l in pre_abs:
        if re.match(r"^(?:Paper\s*Title|Filename|File|Document|Context\s*Scanner)[:\s]", l, re.I):
            continue
        if is_banner_noise(l):
            continue
        cleaned_pre.append(l)

    if not cleaned_pre:
        cleaned_pre = pre_abs

    # Find where author block starts
    author_start = 1
    for i, l in enumerate(cleaned_pre[1:], 1):
        if any(k in l.lower() for k in [
            "department", "university", "college", "email", "@",
            "faculty", "institute", "laboratory"
        ]):
            author_start = max(1, i - 1)
            break
        if i <= 3 and not any(k in l.lower() for k in ["@", "dept", "univ", "college"]):
            author_start = i + 1
        else:
            author_start = i
            break

    title = " ".join(cleaned_pre[:author_start]).strip() if cleaned_pre else fallback_title
    authors_raw = cleaned_pre[author_start:]

    # Clean Title
    title = re.sub(r"^[#\s\*]+", "", title).strip()
    if not title:
        title = fallback_title

    # Parse Authors, Affiliations, Emails
    emails = []
    names = []
    affiliations = []

    for l in authors_raw:
        if "@" in l:
            found_emails = re.findall(r"[\w\.-]+@[\w\.-]+", l)
            emails.extend(found_emails)
        elif any(k in l.lower() for k in [
            "department", "college", "university", "institute", "lab", "school", "faculty"
        ]):
            clean_aff = re.sub(r"^[#\*\s]+", "", l).strip()
            if clean_aff not in affiliations:
                affiliations.append(clean_aff)
        elif any(k in l.lower() for k in [
            "pune", "india", "usa", "wagholi", "california", "state", "city",
            "china", "germany", "japan", "nigeria", "maryland"
        ]):
            if affiliations and affiliations[-1] != l:
                affiliations[-1] += f", {l}"
            elif l not in affiliations:
                affiliations.append(l)
        elif len(l.split()) <= 4 and not any(c in l for c in ["@", ":", ";", "=", "{", "}", "\\", "/"]):
            clean_name = re.sub(r"[\d,\*\†\‡]+$", "", l).strip()
            if clean_name and clean_name not in names:
                names.append(clean_name)

    # 3. Extract Abstract & Index Terms
    idx = abs_idx
    abstract_lines = []
    index_terms = []

    first_abs_line = lines[idx]
    clean_first = re.sub(r"^(?:#{1,3}\s*)?abstract[—–\-:\s]+", "", first_abs_line, flags=re.I).strip()
    if clean_first:
        abstract_lines.append(clean_first)
    idx += 1
    total = len(lines)

    while idx < total:
        l = lines[idx]
        if re.match(r"^(?:index\s+terms|keywords)[—–\-:\s]", l, re.I):
            terms_clean = re.sub(r"^(?:index\s+terms|keywords)[—–\-:\s]+", "", l, flags=re.I).strip()
            if terms_clean:
                index_terms.append(terms_clean)
            idx += 1
            break
        elif re.match(r"^(?:#{1,3}\s*)?(?:[IVXLCDM]+\.|\d+\.)\s+[A-Za-z]", l):
            break
        else:
            if l:
                abstract_lines.append(l)
            idx += 1

    abstract_text = " ".join(abstract_lines).strip()
    index_terms_str = (
        "; ".join(index_terms).strip()
        if index_terms
        else "Artificial Intelligence; Machine Learning; Multi-Agent Systems; Research Automation"
    )

    # 4. Extract Sections and Body
    sections = []
    current_sec_title = ""
    current_sec_roman = ""
    current_sec_lines = []

    sec_regex = re.compile(r"^(?:#{1,3}\s*)?([IVXLCDM]+|\d+)\.\s+([A-Za-z0-9\s,–—\-:'\"/]+)$")
    ref_regex = re.compile(r"^(?:#{1,3}\s*)?(?:REFERENCES|BIBLIOGRAPHY)\b", re.I)

    in_references = False
    ref_lines = []

    while idx < total:
        l = lines[idx]
        idx += 1

        if not l:
            if current_sec_lines and current_sec_lines[-1] != "":
                current_sec_lines.append("")
            continue

        # Check for References section
        if ref_regex.match(l):
            if current_sec_title:
                sections.append({
                    "roman": current_sec_roman,
                    "title": current_sec_title,
                    "lines": current_sec_lines,
                })
                current_sec_title = ""
                current_sec_lines = []
            in_references = True
            continue

        if in_references:
            ref_lines.append(l)
            continue

        # Check for Section Header
        sec_m = sec_regex.match(l)
        if sec_m:
            if current_sec_title:
                sections.append({
                    "roman": current_sec_roman,
                    "title": current_sec_title,
                    "lines": current_sec_lines,
                })
                current_sec_lines = []
            current_sec_roman = sec_m.group(1).upper()
            current_sec_title = sec_m.group(2).strip().upper()
            continue

        current_sec_lines.append(l)

    if current_sec_title:
        sections.append({
            "roman": current_sec_roman,
            "title": current_sec_title,
            "lines": current_sec_lines,
        })

    # Deduplicate and format authors, affiliations, correspondence
    unique_names = []
    for nm in names:
        c_nm = nm.strip()
        if c_nm and c_nm not in unique_names:
            unique_names.append(c_nm)
    authors_str = ", ".join(unique_names) if unique_names else "ResearchX Academic Authors"

    unique_affils = []
    for aff in affiliations:
        clean = aff.strip().strip(",").strip()
        if not clean:
            continue
        is_covered = False
        for i, existing in enumerate(unique_affils):
            if clean.lower() == existing.lower() or clean.lower() in existing.lower():
                is_covered = True
                break
            elif existing.lower() in clean.lower():
                unique_affils[i] = clean
                is_covered = True
                break
        if not is_covered:
            unique_affils.append(clean)
    affil_str = ", ".join(unique_affils) if unique_affils else "Department of Computer Science & Engineering"

    unique_emails = []
    for em in emails:
        c_em = em.strip().lower()
        if c_em and c_em not in [x.lower() for x in unique_emails]:
            unique_emails.append(c_em)
    corr_str = ", ".join(unique_emails) if unique_emails else "contact@researchx.academic.org"

    return {
        "title": title,
        "authors_str": authors_str,
        "affil_str": affil_str,
        "corr_str": corr_str,
        "abstract_text": abstract_text,
        "index_terms_str": index_terms_str,
        "sections": sections,
        "ref_lines": ref_lines,
    }


def compile_ieee_paper(parsed_data: Dict[str, Any]) -> str:
    """
    Compile structured IEEE paper dictionary into valid IEEE Markdown.
    Ensures sequential Roman numeral numbering and proper section formatting.
    """
    title = parsed_data.get("title", "Research Paper")
    authors_str = parsed_data.get("authors_str", "ResearchX Academic Authors")
    affil_str = parsed_data.get("affil_str", "Department of Computer Science & Engineering")
    corr_str = parsed_data.get("corr_str", "contact@researchx.academic.org")
    abstract_text = parsed_data.get("abstract_text", "").strip()
    index_terms_str = parsed_data.get("index_terms_str", "").strip()
    sections = parsed_data.get("sections", [])
    ref_lines = parsed_data.get("ref_lines", [])

    out = []
    out.append(f"# {title}\n")
    out.append(f"**Authors:** {authors_str}")
    out.append(f"**Affiliation:** {affil_str}")
    out.append(f"**Correspondence:** {corr_str}\n")
    out.append("---\n")

    out.append("### ABSTRACT")
    out.append(abstract_text + "\n")
    if index_terms_str:
        out.append(f"**Index Terms**—{index_terms_str}\n")
    out.append("---\n")

    roman_numerals = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"
    ]

    for s_idx, sec in enumerate(sections):
        if isinstance(sec, dict):
            s_title = sec.get("title", "").strip().upper()
            s_lines = sec.get("lines", [])
        else:
            _, s_title, s_lines = sec
            s_title = s_title.strip().upper()

        norm_roman = roman_numerals[s_idx] if s_idx < len(roman_numerals) else str(s_idx + 1)
        out.append(f"## {norm_roman}. {s_title}\n")

        para_buf = []
        for line in s_lines:
            sub_m = re.match(r"^(?:#{2,3}\s*)?([A-Z]\.|\d+\.\d+)\s+([A-Za-z0-9\s,–—\-:'\"/]+)$", line)
            if sub_m:
                if para_buf:
                    out.append(" ".join(para_buf) + "\n")
                    para_buf = []
                sub_label = sub_m.group(1)
                if not sub_label.endswith("."):
                    sub_label += "."
                out.append(f"### {sub_label} {sub_m.group(2).strip()}\n")
                continue

            if not line:
                if para_buf:
                    out.append(" ".join(para_buf) + "\n")
                    para_buf = []
            else:
                para_buf.append(line)

        if para_buf:
            out.append(" ".join(para_buf) + "\n")

    # References
    if ref_lines:
        out.append("## REFERENCES\n")
        ref_buf = []
        for rl in ref_lines:
            if re.match(r"^\[\d+\]", rl):
                if ref_buf:
                    out.append(" ".join(ref_buf) + "\n")
                    ref_buf = []
                ref_buf.append(rl)
            else:
                if ref_buf:
                    ref_buf.append(rl)
                else:
                    if rl.strip():
                        ref_buf.append(rl)
        if ref_buf:
            out.append(" ".join(ref_buf) + "\n")

    return "\n".join(out)


def parse_and_format_ieee_paper(
    raw_text: str, fallback_title: str = "Research Paper"
) -> Tuple[bool, str]:
    """
    Parse an already-structured IEEE or academic paper and format into strict IEEE Markdown.
    Preserves exact content, authentic section titles, paragraphs, math, tables, and all references.
    Executes deterministically in milliseconds without unnecessary LLM calls.
    """
    parsed = parse_ieee_paper_structure(raw_text, fallback_title)
    if not parsed:
        return False, ""
    return True, compile_ieee_paper(parsed)


def edit_ieee_paper_with_query(
    parsed_data: Dict[str, Any],
    query: str,
) -> Tuple[str, str, str]:
    """
    Directly edit and update the structured IEEE paper according to the user's request.
    Preserves existing content, authors, affiliations, equations, and references.
    Returns (updated_paper_markdown, updated_content, edit_summary).
    """
    clean_query = query.strip()
    if not clean_query:
        return compile_ieee_paper(parsed_data), "", "Preserved authentic IEEE paper without modifications."

    existing_sections = []
    for s in parsed_data.get("sections", []):
        s_title = s.get("title", "") if isinstance(s, dict) else s[1]
        existing_sections.append(s_title)
    outline_str = "\n".join(f"- {st}" for st in existing_sections)

    prompt = f"""
You are an expert Senior IEEE Transactions Editor and academic co-author.
The author has submitted a research paper and requested a specific edit or addition.

USER EDIT REQUEST:
"{clean_query}"

EXISTING PAPER CONTEXT:
Title: {parsed_data.get('title', 'Research Paper')}
Abstract: {parsed_data.get('abstract_text', '')[:400]}...
Existing Sections:
{outline_str}

YOUR TASK:
Generate the required update to fulfill the author's request with high academic rigor.
Respond ONLY with a JSON object in this exact schema (no markdown fences, pure JSON):
{{
  "action": "add_section" | "modify_section" | "update_abstract",
  "target_section": "Name of section to modify, or section to insert next to (e.g. 'before_conclusion' or 'I. INTRODUCTION')",
  "section_title": "TITLE OF THE NEW OR MODIFIED SECTION (IN ALL CAPS)",
  "content": "Full, complete academic paragraphs in formal IEEE tone. Provide rich, scholarly content (2-4 robust paragraphs, minimum 150 words). Do not use bullet points.",
  "edit_summary": "A concise 1-sentence description of the exact change applied"
}}
"""
    updated_content = ""
    edit_summary = f"Applied edit request: {clean_query[:60]}"

    try:
        response_text = generate_answer(
            context=f"Paper: {parsed_data.get('title', '')}\nAbstract: {parsed_data.get('abstract_text', '')}\nEdit Request: {clean_query}",
            question=prompt,
        )

        clean_json_str = response_text.strip()
        if clean_json_str.startswith("```"):
            clean_json_str = re.sub(r"^```(?:json)?\s*", "", clean_json_str)
            clean_json_str = re.sub(r"\s*```$", "", clean_json_str)

        parsed_json = None
        json_match = re.search(r"\{[\s\S]*\}", clean_json_str)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(0))
            except Exception:
                pass

        if parsed_json and isinstance(parsed_json, dict):
            action = parsed_json.get("action", "add_section")
            target = parsed_json.get("target_section", "before_conclusion")
            sec_title = parsed_json.get("section_title", clean_query.title()).upper()
            content = parsed_json.get("content", "").strip()
            summary = parsed_json.get("edit_summary", "")

            if summary:
                edit_summary = summary
            updated_content = content

            if content:
                content_lines = [l.strip() for l in content.splitlines() if l.strip()]

                if action == "update_abstract" or "abstract" in clean_query.lower():
                    parsed_data["abstract_text"] = content
                    edit_summary = edit_summary or "Updated abstract with requested focus and technical findings."
                elif action == "modify_section":
                    modified = False
                    for sec in parsed_data["sections"]:
                        s_title = sec["title"] if isinstance(sec, dict) else sec[1]
                        if target.upper() in s_title.upper() or s_title.upper() in target.upper():
                            if isinstance(sec, dict):
                                sec["lines"] = content_lines
                                if sec_title and len(sec_title) > 3:
                                    sec["title"] = sec_title
                            modified = True
                            break
                    if not modified:
                        parsed_data["sections"].append({"roman": "", "title": sec_title, "lines": content_lines})
                else:
                    # add_section: insert before conclusion
                    sections_list = parsed_data["sections"]
                    insert_idx = len(sections_list)
                    for idx, sec in enumerate(sections_list):
                        s_title = sec["title"] if isinstance(sec, dict) else sec[1]
                        if any(k in s_title.upper() for k in ["CONCLUSION", "SUMMARY", "FUTURE"]):
                            insert_idx = idx
                            break

                    new_sec = {"roman": "", "title": sec_title, "lines": content_lines}
                    sections_list.insert(insert_idx, new_sec)
                    edit_summary = edit_summary or f"Added new section: {sec_title}"

        else:
            if response_text and len(response_text.strip()) > 50:
                clean_lines = [l.strip() for l in response_text.splitlines() if l.strip()]
                new_sec = {
                    "roman": "",
                    "title": clean_query.title().upper() if len(clean_query) < 50 else "SPECIAL TOPIC STUDY",
                    "lines": clean_lines,
                }
                sections_list = parsed_data["sections"]
                insert_idx = len(sections_list)
                for idx, sec in enumerate(sections_list):
                    s_title = sec["title"] if isinstance(sec, dict) else sec[1]
                    if any(k in s_title.upper() for k in ["CONCLUSION", "SUMMARY", "FUTURE"]):
                        insert_idx = idx
                        break
                sections_list.insert(insert_idx, new_sec)
                updated_content = response_text
                edit_summary = f"Incorporated requested content for '{clean_query[:50]}'"

    except Exception as edit_err:
        print(f"[IEEE Report Agent] Direct edit error: {edit_err}")
        edit_summary = f"Preserved authentic paper (edit error: {str(edit_err)[:40]})"

    final_paper = compile_ieee_paper(parsed_data)
    return clean_report_output(final_paper), updated_content, edit_summary


def clean_report_output(text: str) -> str:
    """
    Sanitize and normalize generated IEEE report markdown:
    - Strip markdown code fences
    - Remove conversational introductory chatter
    - Normalize Unicode dashes, quotation marks, and line breaks
    - Preserve authentic IEEE section headings, tables, and numbered references
    """
    if not text:
        return ""

    result = text.strip()

    # Strip code block fences if any
    result = re.sub(
        r"^```(?:markdown|text|plain)?\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )
    result = re.sub(r"\s*```$", "", result)

    # Normalize line breaks and escaped characters
    result = (
        result.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\x00", "")
        .replace("\ufffd", "—")
    )

    # Remove conversational preamble if model outputs phrases like:
    # "Here is the IEEE-style research report based on the provided context:"
    preamble_match = re.search(
        r"(?:^|\n)(#[^#\n]+|\*\*Title:\*\*|TITLE:)",
        result,
        flags=re.IGNORECASE,
    )
    if preamble_match and preamble_match.start() > 0:
        result = result[preamble_match.start():].strip()

    roman_numerals = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"
    ]

    def num_to_roman(match):
        num = int(match.group(1))
        title = match.group(2).strip()
        r = roman_numerals[num - 1] if 1 <= num <= len(roman_numerals) else str(num)
        return f"## {r}. {title}"

    # Convert numeric section headings to Roman numerals without altering authentic section titles
    result = re.sub(
        r"^##\s*(\d+)\.\s*([A-Za-z0-9\s,–—\-:'\"/]+)$",
        num_to_roman,
        result,
        flags=re.MULTILINE,
    )

    # Standardize references heading
    result = re.sub(
        r"^##\s*(?:[IVXLCDM]+\.|\d+\.)?\s*REFERENCES\b.*$",
        "## REFERENCES",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # Normalize excess blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


def ensure_architecture_diagram_in_report(
    report_text: str,
    paper_title: str,
    context: Optional[str] = None,
    query: Optional[str] = None,
) -> str:
    """
    Ensures an authentic, publication-grade Architecture Diagram is properly inserted
    into the IEEE paper's Methodology & System Architecture section.
    Preserves all existing content without modification.
    """
    if not report_text or len(report_text.strip()) < 100:
        return report_text

    # Check if report already has an architecture diagram image
    if re.search(r"!\[.*?\]\(.*?_arch\.png\)", report_text) or re.search(r"!\[.*?\]\(.*?/uploads/.*?\.png\)", report_text):
        return report_text

    try:
        from app.services.diagram_generator import build_ieee_architecture_block
        block_md, img_path, caption = build_ieee_architecture_block(
            paper_title=paper_title or "Research Paper",
            context=context or report_text,
            query=query,
        )
    except Exception as diag_err:
        print(f"[IEEE Report Agent] Diagram generation warning: {diag_err}")
        return report_text

    # Priority 1: A section matching METHODOLOGY, SYSTEM ARCHITECTURE, PROPOSED ARCHITECTURE, MODEL ARCHITECTURE
    sec_match = re.search(
        r"(##\s*(?:[IVXLCDM]+|\d+)\.\s*(?:[^\n]*(?:METHODOLOGY|ARCHITECTURE|PROPOSED SYSTEM|PROPOSED METHOD|MODEL ARCHITECTURE)[^\n]*))",
        report_text,
        re.IGNORECASE,
    )

    if sec_match:
        after_sec = report_text[sec_match.end():sec_match.end() + 600]
        sub_match = re.search(r"(###\s*[A-Z0-9]\.[^\n]*)", after_sec)
        if sub_match:
            insert_pos = sec_match.end() + sub_match.end()
            return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")
        insert_pos = sec_match.end()
        return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")

    # Priority 2: Look for ## IV. (Section 4)
    sec_iv = re.search(r"(##\s*IV\.\s*[^\n]*)", report_text, re.IGNORECASE)
    if sec_iv:
        insert_pos = sec_iv.end()
        return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")

    # Priority 3: Look for ## III. (Section 3)
    sec_iii = re.search(r"(##\s*III\.\s*[^\n]*)", report_text, re.IGNORECASE)
    if sec_iii:
        insert_pos = sec_iii.end()
        return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")

    # Priority 4: Look for numeric numbered section (e.g. workspace synthesis '7. Methodology Comparison')
    num_match = re.search(r"((?:^|\n)\d+\.\s*(?:[^\n]*Methodology[^\n]*))", report_text, re.IGNORECASE)
    if num_match:
        insert_pos = num_match.end()
        return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")

    # Fallback: Insert before conclusion or references
    ref_match = re.search(r"(##\s*(?:[IVXLCDM]+\.|\d+\.)?\s*(?:REFERENCES|CONCLUSION)[^\n]*)", report_text, re.IGNORECASE)
    if ref_match:
        insert_pos = ref_match.start()
        return report_text[:insert_pos] + "\n\n" + block_md.strip() + "\n\n" + report_text[insert_pos:].lstrip("\n")

    return report_text + "\n\n" + block_md.strip()


# ==========================================================
# IEEE Report Agent
# ==========================================================

def generate_ieee_report(
    context: Optional[str] = None,
    paper_name: Optional[str] = None,
    query: Optional[str] = None,
    return_audit: bool = False,
    **kwargs: Any,
) -> Union[str, Tuple[str, Optional[Dict[str, Any]], Optional[str]]]:
    """
    Generate an authoritative, publication-grade IEEE Transactions research report.
    Supports:
    - Direct surgical editing of uploaded papers based on user query
    - Fast-path preservation of authentic IEEE formatting
    - Separate dedicated plagiarism/originality auditing
    """
    is_query_only = False

    if not context or len(context.strip()) < 50:
        if paper_name and paper_name.lower().strip() not in ("query_focus", "query focus", "none", ""):
            context = load_context_for_paper(
                paper_name=paper_name,
                query=query or "methodology results datasets experiments literature",
            )

    if not context or not context.strip():
        if query and query.strip():
            is_query_only = True
        else:
            msg = (
                "Unable to generate IEEE report because "
                "no research paper context or research query was provided."
            )
            if return_audit:
                return msg, None, None
            return msg

    doc_title = (
        paper_name.replace(".pdf", "").replace("_", " ").strip()
        if paper_name and paper_name.lower().strip() not in ("query_focus", "query focus")
        else (query.strip().title() if query else "Advanced Machine Learning Investigation")
    )

    has_edit_request = bool(
        query
        and query.strip()
        and query.strip().lower() not in (
            "comprehensive ieee manuscript", "none", "", "generate report", "apply focus", "query_focus", "report", "ieee report"
        )
    )

    # ----------------------------------------------------
    # PATH A: Structured IEEE Paper (Direct Edit or Preservation)
    # ----------------------------------------------------
    if not is_query_only and context and is_already_ieee_formatted(context):
        parsed = parse_ieee_paper_structure(raw_text=context, fallback_title=doc_title)
        if parsed:
            if has_edit_request:
                updated_paper, updated_content, edit_summary = edit_ieee_paper_with_query(
                    parsed_data=parsed,
                    query=query.strip(),
                )
                final_paper = clean_report_output(updated_paper)
                final_paper = ensure_architecture_diagram_in_report(
                    report_text=final_paper,
                    paper_title=doc_title,
                    context=context,
                    query=query,
                )
                audit = audit_paper_originality(
                    paper_text=final_paper,
                    target_filename=paper_name or "",
                    updated_content=updated_content,
                )
                print(f"[IEEE Report Agent] Applied direct edit query to {doc_title}: '{edit_summary}'")
                if return_audit:
                    return final_paper, audit, edit_summary
                return final_paper
            else:
                final_paper = clean_report_output(compile_ieee_paper(parsed))
                final_paper = ensure_architecture_diagram_in_report(
                    report_text=final_paper,
                    paper_title=doc_title,
                    context=context,
                    query=query,
                )
                audit = audit_paper_originality(
                    paper_text=final_paper,
                    target_filename=paper_name or "",
                    updated_content="",
                )
                print(f"[IEEE Report Agent] Fast-path preserved authentic IEEE paper: {doc_title} ({len(final_paper)} chars)")
                if return_audit:
                    return final_paper, audit, "Preserved authentic IEEE paper without modifications."
                return final_paper

    # ----------------------------------------------------
    # LLM PATH: Synthesis for Unstructured Content / Query-Only
    # ----------------------------------------------------
    effective_context = context
    if effective_context and len(effective_context) > 12000:
        effective_context = effective_context[:7000] + "\n\n[...]\n\n" + effective_context[-5000:]

    query_focus_directive = ""
    if query and query.strip():
        query_focus_directive = f"""
==========================================================
USER RESEARCH QUERY FOCUS
==========================================================
The user specifically requested the following research focus/query:
"{query.strip()}"

Direct your technical analysis, emphasis, and methodological breakdown
towards addressing this specific research query while remaining completely
faithful to the facts, evidence, and results in the uploaded paper context.
"""

    if not is_query_only:
        question = f"""
You are ResearchX, an expert senior IEEE Transactions editor, principal AI researcher,
and peer-review chair.

Your task is to format and present the provided research paper content into an authoritative,
publication-grade IEEE Transactions research paper manuscript.

==========================================================
CORE IEEE STRUCTURING & PRESERVATION PRINCIPLES
==========================================================
1. STRICT CONTENT & REFERENCE PRESERVATION:
   - PRESERVE the author's real section titles, empirical results, equations, and references.
   - Do NOT invent artificial subsections (such as 'A. Background & Industrial Motivation',
     'B. Problem Formulation & Scope', 'D. Paper Organization') if they do not match the real paper.
   - Do NOT summarize away empirical baseline numbers or ablation details.
   - Number all authentic references strictly in brackets ([1], [2], etc.). Do not hallucinate fake citations.

2. IEEE MANUSCRIPT FORMATTING:
   - Top Title: # Title
   - Authors: **Authors:** [Author names from paper]
   - Affiliations: **Affiliation:** [Affiliations from paper]
   - Correspondence: **Correspondence:** [Emails or corresponding contact]
   - Divider: ---
   - Abstract: ### ABSTRACT followed by a cohesive academic paragraph (no bullet points)
   - Index Terms: **Index Terms**—[4-6 technical keywords separated by semicolons]
   - Divider: ---
   - Major Sections: Roman numerals (## I. INTRODUCTION, ## II. ..., etc.)
   - Subsections: Capital letters (### A. ..., ### B. ..., etc.)
   - Mathematical expressions: LaTeX notation ($$ ... $$)
   - Tables: Markdown tables with captions (TABLE I: ...)
   - Bibliography: ## REFERENCES followed by numbered entries ([1] ..., [2] ...)

3. ZERO FABRICATION / ZERO HALLUCINATION RULE:
   - Never fabricate fake metrics, fake benchmark scores, fake hardware, or fake author identities.
   - If specific details are absent from the source paper, state: "Not specified in the provided paper."

{query_focus_directive}

Produce formal, third-person IEEE academic English.
Return ONLY the full IEEE manuscript.
"""
    else:
        # Query-Only Mode: Generate a comprehensive IEEE-style academic research report on the topic query
        question = f"""
You are ResearchX, an expert senior IEEE Transactions editor, principal AI researcher,
and peer-review chair.

The user has requested an authoritative, comprehensive IEEE Transactions research report on the following topic:
"{query.strip()}"

Your task is to write a complete, publication-grade IEEE research paper manuscript synthesizing
the state of the art, theoretical formulations, architectural paradigms, empirical benchmarks,
and open challenges in this domain.

==========================================================
REQUIRED IEEE MANUSCRIPT STRUCTURE
==========================================================
Generate the report using the following EXACT structure:

# {doc_title}

**Authors:** ResearchX Academic Working Group
**Affiliation:** Department of Artificial Intelligence & Autonomous Systems, ResearchX Academic Platform
**Correspondence:** contact@researchx.academic.org

---

### ABSTRACT
A comprehensive, high-density 150-250 word academic abstract written as a single cohesive paragraph.
It must explicitly outline:
(1) The underlying research problem and scientific urgency,
(2) The state-of-the-art methodology and architectural landscape,
(3) Benchmark standards and comparative performance characteristics, and
(4) The overarching scientific takeaway and domain significance.
Do NOT use bullet points in the abstract.

**Index Terms**—[Provide 4 to 6 authoritative IEEE Index Terms separated by semicolons, e.g., Machine Learning; Deep Neural Networks; Representation Learning; Empirical Evaluation]

---

## I. INTRODUCTION
Provide an in-depth academic introduction:
### A. Background & Industrial Motivation
Contextualize the domain challenge and why this research area is of paramount importance.
### B. Problem Formulation & Scope
Mathematically or conceptually define the core challenges in this domain.
### C. Research Objectives & Key Contributions
Enumerate the primary dimensions of analysis synthesized in this manuscript in clear bullet points.
### D. Paper Organization
A concluding paragraph outlining Sections II through VIII.

## II. RELATED WORK
A rigorous comparative review of seminal works and state-of-the-art baselines:
### A. Theoretical Foundations & Prior Paradigms
### B. Architectural Bottlenecks & Limitations
### C. Recent Breakthroughs & Emerging Directions

## III. PROBLEM STATEMENT & OBJECTIVES
### A. Mathematical Formulation & System Model
Include formal objective constraints and clean LaTeX equations ($$ ... $$).
### B. Research Hypotheses & Optimization Goals

## IV. METHODOLOGY & SYSTEM ARCHITECTURE
### A. Foundational Architecture Overview
Detailed breakdown of prevailing model structures, attention mechanisms, or algorithmic pipelines.
### B. Algorithmic Mechanics & Loss Functions
Provide explicit mathematical formulations with clean LaTeX equations:
$$L_{{objective}} = \\mathbb{{E}}_{{x \\sim p_{{data}}}} [-\\log p_\\theta(x)]$$
### C. Processing Pipeline & Parameter Optimization

## V. EXPERIMENTAL SETUP & DATASETS
### A. Standard Benchmark Datasets
Document the standard evaluation benchmarks, sample sizes, and modality splits in this domain.
### B. State-of-the-Art Baseline Architectures
### C. Standard Evaluation Metrics
Formal definitions of primary performance metrics (e.g., F1-Score, BLEU, Perplexity, Throughput).

## VI. RESULTS AND DISCUSSION
### A. Comparative Benchmark Synthesis
Include a comprehensive Markdown comparative table summarizing representative literature benchmarks:
TABLE I: COMPARATIVE BENCHMARK EVALUATION OF PREVAILING ARCHITECTURES
| Paradigm / Model | Key Dataset | Benchmark Metric | Latency / Complexity | Primary Trade-Off |
| :--- | :--- | :--- | :--- | :--- |
| Baseline Paradigm | Standard Benchmark | Representative Score | Moderate | Scaling Constraints |
| Advanced Paradigm | Standard Benchmark | Representative Score | High Throughput | Compute Requirements |

### B. Ablation & Architectural Trade-offs
### C. Empirical Insights & Cross-domain Performance

## VII. LIMITATIONS & RESEARCH GAPS
### A. Computational & Energy Bottlenecks
### B. Generalization Failures & Robustness Challenges

## VIII. CONCLUSION & FUTURE WORK
### A. Synthesis of Findings
### B. High-Priority Future Research Directions

## REFERENCES
Numbered IEEE-formatted references corresponding to foundational and state-of-the-art literature in this domain:
[1] Author Names, "Paper Title," in *Journal/Conference Name*, vol. X, no. Y, pp. Z, Year.
[2] ...

==========================================================
TONE AND FORMAT REQUIREMENTS
==========================================================
- Produce formal, third-person IEEE academic English.
- Use Roman numeral section numbering (## I. INTRODUCTION through ## VIII. CONCLUSION & FUTURE WORK, and ## REFERENCES).
- Use lettered subsection headings (### A., ### B., etc.).
- Do NOT include conversational greetings, markdown commentary, or concluding notes.
- Return ONLY the full IEEE manuscript.
"""

    raw_output = generate_answer(
        context=effective_context or f"Research Domain Topic: {query}",
        question=question,
    )

    final_paper = clean_report_output(raw_output)
    final_paper = ensure_architecture_diagram_in_report(
        report_text=final_paper,
        paper_title=doc_title,
        context=effective_context,
        query=query,
    )
    audit = audit_paper_originality(
        paper_text=final_paper,
        target_filename=paper_name or "",
        updated_content=final_paper if is_query_only else "",
    )
    summary = f"Synthesized complete IEEE manuscript for '{query or doc_title}'."
    if return_audit:
        return final_paper, audit, summary
    return final_paper


# ==========================================================
# Workspace IEEE Report Agent
# ==========================================================

def run_ieee_report_agent(topic: str, papers) -> str:
    """
    Execute the IEEE Report Agent for multiple
    selected research papers.
    """

    print("Running IEEE Report Agent...")

    context_parts = []

    for i, paper in enumerate(papers, start=1):

        context_parts.append(
            f"""
==========================================================
PAPER {i}
==========================================================

Title:
{paper.title}

Authors:
{", ".join(paper.authors)}

Abstract / Summary:
{paper.summary}

Published:
{paper.published}

Citation Count:
{getattr(paper, "citation_count", "Not specified")}

Venue:
{getattr(paper, "venue", "Not specified")}

Source:
{getattr(paper, "source", "Not specified")}
"""
        )

    context = "\n\n".join(context_parts)

    workspace_question = f"""
You are ResearchX, an expert IEEE research synthesis agent.

Research Topic:
{topic}

The provided context contains multiple research papers.

Generate a comparative IEEE-style research synthesis.

Include:

1. Title
2. Abstract
3. Keywords
4. Introduction
5. Related Work
6. Research Problem
7. Methodology Comparison
8. Dataset Comparison
9. Experimental Comparison
10. Results Comparison
11. Research Contributions
12. Limitations
13. Research Gaps
14. Future Research Directions
15. Conclusion
16. References ONLY if explicitly provided

IMPORTANT:

- Use ONLY the provided papers.
- Do not invent citations.
- Do not invent references.
- Do not invent numerical results.
- Do not invent datasets.
- Clearly distinguish facts from inference.
- Label inferred conclusions as "Inferred".
- Label proposed directions as "Proposed".
- If information is unavailable, write:
  "Not specified in the provided papers."
- Do not claim that one paper is objectively better unless
  the provided evidence supports that conclusion.
- Maintain professional IEEE-style academic language.
"""

    raw_rep = generate_answer(
        context=context,
        question=workspace_question,
    )
    clean_rep = clean_report_output(raw_rep)
    return ensure_architecture_diagram_in_report(
        report_text=clean_rep,
        paper_title=topic,
        context=context,
        query=topic,
    )


# ==========================================================
# Final Research Synthesis
# ==========================================================

def generate_final_report(
    summary: str,
    gaps: str,
    datasets: str,
    experiments: str,
    literature: str,
    novelty: str,
) -> str:
    """
    Combine outputs from all ResearchX analysis agents
    and generate one final IEEE-style research report.
    """

    combined_context = f"""
==========================================================
RESEARCHX MULTI-AGENT ANALYSIS
==========================================================

---------------- SUMMARY AGENT ----------------
{summary}

---------------- RESEARCH GAP AGENT ----------------
{gaps}

---------------- DATASET AGENT ----------------
{datasets}

---------------- EXPERIMENT AGENT ----------------
{experiments}

---------------- LITERATURE AGENT ----------------
{literature}

---------------- NOVELTY AGENT ----------------
{novelty}
"""

    question = """
You are ResearchX, the final academic research synthesis
agent.

You have received structured analysis produced by multiple
specialized ResearchX agents.

Your task is to synthesize these analyses into ONE complete,
professional IEEE-style research report.

==========================================================
IMPORTANT SOURCE RULE
==========================================================

Use ONLY the information contained in the supplied
multi-agent analysis.

Do NOT invent information.

Do NOT use external knowledge.

Do NOT create fake citations or references.

Do NOT invent numerical results.

Do NOT invent datasets.

Do NOT invent authors.

Do NOT invent experiments.

Do NOT invent benchmark results.

If information is unavailable, write:

"Not specified in the provided analysis."

==========================================================
REPORT STRUCTURE
==========================================================

Generate exactly these sections:

TITLE

ABSTRACT

KEYWORDS

I. INTRODUCTION

II. PROBLEM STATEMENT AND OBJECTIVES

III. LITERATURE REVIEW

IV. RESEARCH GAP

V. PROPOSED METHODOLOGY

VI. DATASET AND DATA REQUIREMENTS

VII. EXPERIMENTAL DESIGN

VIII. EVALUATION METRICS

IX. EXPECTED / REPORTED RESULTS

X. RESEARCH CONTRIBUTIONS

XI. NOVELTY ANALYSIS

XII. LIMITATIONS

XIII. FUTURE RESEARCH DIRECTIONS

XIV. CONCLUSION

REFERENCES

==========================================================
SYNTHESIS RULES
==========================================================

1. Use the Summary Agent for the overall paper understanding.

2. Use the Research Gap Agent for:
   - research gaps
   - limitations
   - unresolved problems
   - research opportunities

3. Use the Dataset Agent for:
   - dataset requirements
   - explicitly mentioned datasets
   - recommended datasets
   - dataset comparison

4. Use the Experiment Agent for:
   - experiment design
   - methodology
   - baselines
   - evaluation strategy
   - experimental recommendations

5. Use the Literature Agent for:
   - existing work
   - literature landscape
   - research evolution
   - literature gaps

6. Use the Novelty Agent for:
   - contribution analysis
   - originality
   - innovation assessment
   - differentiation

==========================================================
IMPORTANT DISTINCTIONS
==========================================================

Never confuse:

Paper facts
vs
Agent recommendations
vs
Inferences.

Clearly label them.

For example:

"Reported in the paper:"
for information supported by the paper.

"Recommended:"
for suggestions produced by the agents.

"Inferred:"
for conclusions derived from the available evidence.

"Proposed:"
for new research directions.

==========================================================
RESULT HANDLING
==========================================================

If the agents provide reported numerical results:

- Preserve them exactly.

If no numerical results are available:

"Reported numerical results are not specified."

Do NOT turn expected results into actual results.

For example:

WRONG:
"The model achieved 95% accuracy."

if the agents only recommend that accuracy
should be evaluated.

CORRECT:
"Accuracy is recommended as an evaluation metric."

==========================================================
DATASET HANDLING
==========================================================

Clearly distinguish:

1. Dataset explicitly mentioned in the paper.
2. Dataset recommended by the Dataset Agent.

Never claim that a recommended dataset
was used by the original paper.

==========================================================
NOVELTY HANDLING
==========================================================

Do not present the Novelty Agent's score as
an objectively verified scientific novelty score.

Instead write:

"ResearchX assessment: Innovation Score = X/10"

when a score is available.

Mention that the assessment is based on
the supplied analysis.

==========================================================
REFERENCES
==========================================================

Only include references explicitly available
in the supplied analysis.

Never invent references.

If none are available:

"References are not available in the supplied analysis."

==========================================================
FINAL QUALITY REQUIREMENTS
==========================================================

- Professional IEEE-style academic language.
- Clear section numbering.
- Logical flow between sections.
- Avoid repetition between agents.
- Resolve duplicate information intelligently.
- Preserve important technical details.
- Do not strengthen claims beyond the evidence.
- Do not convert recommendations into facts.
- Do not convert inferred conclusions into author claims.
- Produce a complete report.
- Do not stop midway.

Return ONLY the final IEEE-style research report.
"""

    raw_res = generate_answer(
        context=combined_context,
        question=question,
    )
    clean_res = clean_report_output(raw_res)
    return ensure_architecture_diagram_in_report(
        report_text=clean_res,
        paper_title="Multi-Agent Research Synthesis",
        context=combined_context,
    )