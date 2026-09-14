import os
import re
from typing import Any, Dict, List, Optional

from app.agents.coordinator import load_context_for_paper
from app.llm.gemini import generate_answer


def clean_presentation_output(text: str) -> str:
    """
    Sanitize LLM presentation text while preserving structured slide headers,
    metadata fields, bullet points, and speaker notes.
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

    # Normalize multiple separators
    result = re.sub(r"={4,}", "======================================================", result)
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Strip any conversational preamble before the first slide header
    first_slide_match = re.search(r"(?:={4,}\s*)?###\s*Slide\s*1\b", result, re.IGNORECASE)
    if first_slide_match:
        result = result[first_slide_match.start():]

    return result.strip()


def generate_presentation(
    context: Optional[str] = None,
    paper_name: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Generate an authoritative, publication-grade IEEE/ACM style PowerPoint presentation
    grounded strictly in the uploaded research paper context.
    """
    doc_title = (
        paper_name
        or kwargs.get("title")
        or kwargs.get("document_name")
        or "Uploaded Research Paper"
    )

    content = (
        context
        or kwargs.get("text", "")
        or kwargs.get("paper_context", "")
        or ""
    )

    # If context is not passed or sparse, load authentic context from DB/disk
    if not content or len(content.strip()) < 100:
        retrieved = load_context_for_paper(
            paper_name=doc_title,
            query="abstract methodology experiments benchmark results conclusion",
            pdf_url=kwargs.get("pdf_url"),
        )
        if retrieved and len(retrieved.strip()) >= 100:
            content = retrieved

    if not content or len(content.strip()) < 50:
        return (
            "Insufficient research paper context available to generate presentation slides. "
            "Please verify that the target document has been properly uploaded."
        )

    # Extract clean context slice (up to 35,000 characters for deep technical grounding)
    paper_context = content[:35000]

    question = f"""You are the Senior IEEE & ACM Academic Presentation Designer for ResearchX.
Your task is to analyze the provided research paper ("{doc_title}") and construct an authentic, mathematically and empirically precise, 11-slide conference presentation deck for a high-stakes research defense.

CRITICAL ACCURACY & GROUNDING RULES:
1. STRICT AUTHENTICITY: Rely EXCLUSIVELY on the provided research paper context. Never extrapolate, hallucinate, or fabricate author names, institutional affiliations, model names, datasets, evaluation metrics, or performance benchmarks.
2. REAL TECHNICAL CONTENT: If specific configuration parameters (e.g. batch size, learning rate, GPU specs, sample splits) or exact metrics (e.g. Accuracy %, F1-score, BLEU, mAP, Latency) are stated in the paper, INCLUDE THEM.
3. NO LAZY PLACEHOLDERS: NEVER output 'Not available in the uploaded paper', 'N/A', or '[Insert Title]'. If an author affiliation is omitted, write the authors' names and focus on the technical research domain.
4. LOGICAL PROGRESSION: Maintain a rigorous conference presentation flow:
   - Slide 1: Paper Title, Authors, Affiliation / Venue, Domain
   - Slide 2: Executive Motivation & Scientific Context
   - Slide 3: Problem Formulation & Core Research Objectives
   - Slide 4: State-of-the-Art & Limitations of Prior Approaches
   - Slide 5: Proposed Architecture & Theoretical Framework
   - Slide 6: Algorithmic Details, Pipeline & Mathematical Formulation
   - Slide 7: Experimental Setup, Datasets, Hardware & Baselines
   - Slide 8: Empirical Results, Quantitative Metrics & Benchmark Performance
   - Slide 9: Comparative Analysis, Ablation Studies & Statistical Insights
   - Slide 10: Novel Research Contributions & Key Technical Advantages
   - Slide 11: Limitations, Open Challenges & Future Directions

REQUIRED SLIDE OUTPUT FORMAT:
Output MUST follow this exact structure for each slide from 1 to 11:

======================================================
### Slide 1: {doc_title}
**Category:** Title & Identification
**Slide Title:** {doc_title}
**Takeaway:** Comprehensive investigation and evaluation presented for academic defense.
**Bullet Points:**
- **Paper Title:** [Exact title from paper]
- **Authors & Affiliation:** [Exact authors and institutions from paper]
- **Target Venue / Domain:** [Domain or publication venue if identified]
- **Core Research Theme:** [1-sentence summary of the research topic]
**Speaker Notes:**
Welcome everyone. Today I will be presenting our research investigation into this work, detailing its methodology, experimental findings, and core contributions.

======================================================
### Slide 2: Research Motivation & Scientific Context
**Category:** Research Motivation
**Slide Title:** Research Motivation & Real-World Context
**Takeaway:** [Impactful 1-sentence statement on why this research problem is critical]
**Bullet Points:**
- **Scientific Challenge:** [Main real-world or theoretical challenge addressed]
- **Industry & Academic Urgency:** [Why existing paradigms fail in practice]
- **Critical Bottleneck:** [The core technical bottleneck described in the paper]
- **Research Opportunity:** [The strategic opportunity unlocked by solving this challenge]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 2]

======================================================
### Slide 3: Problem Formulation & Objectives
**Category:** Problem Definition
**Slide Title:** Problem Formulation & Core Objectives
**Takeaway:** [Clear 1-sentence statement of the primary research objective]
**Bullet Points:**
- **Primary Objective:** [Primary research goal established by the authors]
- **Secondary Aims:** [Specific supporting sub-goals or hypotheses]
- **Theoretical Scope:** [Boundaries and target environment defined in the paper]
- **Expected Outcome:** [Intended algorithmic or empirical deliverables]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 3]

======================================================
### Slide 4: Related Work & Prior Bottlenecks
**Category:** Literature Landscape
**Slide Title:** Related Work & Limitations of Existing Methods
**Takeaway:** [1-sentence summary of how prior approaches fall short]
**Bullet Points:**
- **Foundational Approaches:** [Key prior methods or frameworks cited in the paper]
- **Inherent Constraints:** [Core technical limitations of existing algorithms]
- **Efficiency Bottlenecks:** [Computational, memory, or architectural overheads]
- **Identified Research Gap:** [Specific gap this paper aims to bridge]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 4]

======================================================
### Slide 5: Proposed Architecture & Theoretical Framework
**Category:** System Architecture
**Slide Title:** Proposed Architecture & Theoretical Framework
**Takeaway:** [1-sentence summary of the architectural innovation]
**Bullet Points:**
- **System Architecture:** [High-level structural design and module breakdown]
- **Core Methodology:** [Underlying theoretical or mathematical principle]
- **Data Flow & Pipeline:** [How inputs are processed, transformed, and routed]
- **Design Philosophy:** [Key algorithmic choice ensuring scalability or accuracy]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 5]

======================================================
### Slide 6: Algorithmic Details & Technical Implementation
**Category:** Technical Implementation
**Slide Title:** Algorithmic Details & Technical Implementation
**Takeaway:** [1-sentence summary of the implementation or algorithm]
**Bullet Points:**
- **Core Algorithm:** [Step-by-step logic, equations, or optimization routines]
- **Loss Functions & Formulations:** [Specific objective functions or criteria used]
- **Hyperparameters & Dynamics:** [Learning rates, optimizer, layers, or thresholds]
- **Implementation Highlights:** [Frameworks, parallelization, or specialized routines]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 6]

======================================================
### Slide 7: Experimental Setup, Datasets & Baselines
**Category:** Experimental Design
**Slide Title:** Experimental Setup, Datasets & Baselines
**Takeaway:** [1-sentence summary of the empirical validation protocol]
**Bullet Points:**
- **Benchmark Datasets:** [Exact dataset names, sample splits, and characteristics]
- **Baseline Models:** [Exact state-of-the-art models compared against]
- **Evaluation Metrics:** [Exact quantitative metrics used (e.g. Accuracy, F1, Loss, Latency)]
- **Hardware & Environment:** [Execution platform, GPU/CPU setup, or simulation environment]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 7]

======================================================
### Slide 8: Empirical Results & Benchmark Performance
**Category:** Empirical Results
**Slide Title:** Empirical Results & Quantitative Benchmark Performance
**Takeaway:** [1-sentence summary of the standout quantitative performance]
**Bullet Points:**
- **Primary Performance:** [Exact score / accuracy / metric achieved by the proposed method]
- **Direct Baseline Comparison:** [Numerical margin of victory over baseline competitors]
- **Efficiency Metrics:** [Training time, inference latency, or parameter efficiency]
- **Empirical Significance:** [Statistical robustness and consistency across trials]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 8]

======================================================
### Slide 9: Comparative Analysis & Ablation Insights
**Category:** Empirical Evaluation
**Slide Title:** Comparative Analysis & Ablation Insights
**Takeaway:** [1-sentence summary of component importance from ablations]
**Bullet Points:**
- **Ablation Findings:** [Which specific module or component yielded the highest gain]
- **Sensitivity Analysis:** [Robustness across variations in hyperparameter settings]
- **Failure Cases & Outliers:** [Scenarios where performance degradation was observed]
- **Convergence Behavior:** [Stability during optimization and scaling]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 9]

======================================================
### Slide 10: Novel Contributions & Key Advantages
**Category:** Research Innovation
**Slide Title:** Novel Contributions & Key Technical Advantages
**Takeaway:** [1-sentence summary of the primary academic innovations]
**Bullet Points:**
- **Primary Innovation:** [The most novel algorithmic or structural breakthrough]
- **Theoretical Advance:** [New mathematical insight, proof, or conceptual advance]
- **Practical Utility:** [Real-world deployment advantages and operational gains]
- **Scholarly Impact:** [How this work advances the state of the art in the domain]
**Speaker Notes:**
[2-3 professional sentences providing the spoken presentation narrative for Slide 10]

======================================================
### Slide 11: Limitations & Future Research Directions
**Category:** Conclusion & Roadmap
**Slide Title:** Limitations, Conclusion & Future Directions
**Takeaway:** [1-sentence synthesis of concluding takeaway and future potential]
**Bullet Points:**
- **Identified Limitations:** [Honest technical constraints or boundary conditions]
- **Summary of Findings:** [Final synthesis of verified hypotheses and deliverables]
- **Immediate Future Work:** [Concrete technical extensions proposed by the authors]
- **Long-term Vision:** [Broader impact on the academic and industrial ecosystem]
**Speaker Notes:**
[2-3 professional sentences providing the spoken conclusion for the presentation]
======================================================

Formatting Constraints:
- Exactly 11 slides following this template.
- 3 to 5 bullet points per slide.
- Every bullet MUST follow: - **[Concept]:** [Detailed explanation with facts/numbers].
- Keep each bullet between 12 and 28 words.
- Speaker Notes MUST be 2 to 3 polished sentences suitable for live presentation.
- Use ONLY facts from the uploaded paper. NEVER invent facts.
"""

    raw_output = generate_answer(
        context=paper_context,
        question=question,
    )

    return clean_presentation_output(raw_output)


# ==========================================================
# Workspace PPT Generator Agent
# ==========================================================

def run_ppt_agent(topic: str, papers: Any) -> str:
    """
    Execute the PPT Generator Agent across a workspace topic or multi-paper set.
    """
    print(f"Running PPT Generator Agent for topic: {topic}...")

    if not papers:
        return generate_presentation(paper_name=topic)

    if isinstance(papers, list):
        paper_summaries = []
        for p in papers:
            if isinstance(p, dict):
                title = p.get("title") or p.get("filename") or "Untitled Paper"
                summary = p.get("summary") or p.get("text", "")[:2000]
                authors = ", ".join(p.get("authors", [])) if isinstance(p.get("authors"), list) else str(p.get("authors", ""))
                published = p.get("published", "")
            else:
                title = getattr(p, "title", "Untitled Paper")
                summary = getattr(p, "summary", "") or getattr(p, "text", "")[:2000]
                authors = ", ".join(getattr(p, "authors", [])) if hasattr(p, "authors") and isinstance(p.authors, list) else ""
                published = getattr(p, "published", "")

            paper_summaries.append(
                f"Title: {title}\nAuthors: {authors}\nPublished: {published}\nSummary: {summary}"
            )

        context = "\n\n---\n\n".join(paper_summaries)
        first_title = (
            papers[0].get("title", topic)
            if isinstance(papers[0], dict)
            else getattr(papers[0], "title", topic)
        )
        return generate_presentation(context=context, paper_name=first_title)

    return generate_presentation(paper_name=topic)