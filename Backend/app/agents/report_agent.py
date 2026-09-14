import os
import re
from typing import Any, Dict, List, Optional

from app.agents.coordinator import load_context_for_paper
from app.llm.gemini import generate_answer


def clean_report_output(text: str) -> str:
    """
    Sanitize and normalize generated IEEE report markdown:
    - Strip markdown code fences
    - Remove conversational introductory chatter
    - Normalize Unicode dashes, quotation marks, and line breaks
    - Preserve IEEE section headings, tables, and numbered references
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

    # Normalize canonical IEEE Roman numeral section headings
    result = re.sub(
        r"^##\s*(?:I|\b1)\b\.?\s*INTRODUCTION.*$",
        "## I. INTRODUCTION",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:II|\b2)\b\.?\s*RELATED.*$",
        "## II. RELATED WORK",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:III|\b3)\b\.?\s*(?:PROBLEM|SYSTEM\s*MODEL).*$",
        "## III. PROBLEM STATEMENT & OBJECTIVES",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:IV|\b4)\b\.?\s*METHODOLOGY.*$",
        "## IV. METHODOLOGY & SYSTEM ARCHITECTURE",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:V|\b5)\b\.?\s*(?:EXPERIMENTAL|EXPERIMENTS).*$",
        "## V. EXPERIMENTAL SETUP & DATASETS",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:VI|\b6)\b\.?\s*RESULTS.*$",
        "## VI. RESULTS AND DISCUSSION",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:VII|\b7)\b\.?\s*LIMITATIONS.*$",
        "## VII. LIMITATIONS & RESEARCH GAPS",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:VIII|\b8)\b\.?\s*CONCLUSION.*$",
        "## VIII. CONCLUSION & FUTURE WORK",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    result = re.sub(
        r"^##\s*(?:IX|\b9|\bREFERENCES\b).*REFERENCES.*$",
        "## REFERENCES",
        result,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # Normalize excess blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


# ==========================================================
# IEEE Report Agent
# ==========================================================

def generate_ieee_report(
    context: Optional[str] = None,
    paper_name: Optional[str] = None,
    query: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Generate an authoritative, publication-grade IEEE Transactions research report
    following the official IEEE manuscript structure.
    
    Core Principles:
    - The source PDF is the SOURCE OF RESEARCH CONTENT, not the formatting template.
    - Regardless of whether the source PDF is single-column, has non-standard headings,
      or lacks standard sections, the output MUST be restructured into the official
      IEEE Transactions layout (Sections I through VIII + REFERENCES).
    - If no PDF is provided, supports Query-Only topic research mode.
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
            return (
                "Unable to generate IEEE report because "
                "no research paper context or research query was provided."
            )

    doc_title = (
        paper_name.replace(".pdf", "").replace("_", " ").strip()
        if paper_name and paper_name.lower().strip() not in ("query_focus", "query focus")
        else (query.strip().title() if query else "Advanced Machine Learning Investigation")
    )

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

Your task is to convert and restructure the provided research paper content into a complete,
authoritative, publication-grade IEEE Transactions research paper manuscript.

==========================================================
CORE IEEE STRUCTURING PRINCIPLES
==========================================================
1. SOURCE CONTENT vs. IEEE TEMPLATE:
   The uploaded PDF is ONLY the source of factual research content, NOT the formatting template.
   Even if the uploaded PDF:
   - is not in IEEE format,
   - uses a medical, physics, or alternative journal format,
   - is a single-column or unformatted preprint document,
   - uses different section names or lacks standard academic sections,
   - has disorganized or fragmented text,
   You MUST actively reorganize and synthesize the extracted facts into the strict, official
   IEEE Transactions manuscript structure defined below.

2. MISSING SECTIONS & SECTION RESTRUCTURING:
   Creating missing standard IEEE sections based on available content is REQUIRED:
   - If limitations are scattered or unheaded, group them under "VII. LIMITATIONS & RESEARCH GAPS".
   - If datasets or split ratios are mentioned casually in the text, organize them under "V. EXPERIMENTAL SETUP & DATASETS".
   - If baseline models and ablation numbers appear throughout the text, assemble them into the Markdown comparative table in "VI. RESULTS AND DISCUSSION".

3. ZERO FABRICATION / ZERO HALLUCINATION RULE:
   - While you MUST restructure existing facts into the IEEE format, you must NEVER fabricate or hallucinate
     fake metrics, fake benchmark scores, fake hardware, or fake author identities.
   - If specific details (e.g., exact hardware configuration, learning rate, dataset split numbers)
     are absent from the source paper, explicitly state:
     "Not specified in the provided paper."

{query_focus_directive}

==========================================================
REQUIRED IEEE MANUSCRIPT STRUCTURE
==========================================================
Generate the report using the following EXACT structure:

# {doc_title}

**Authors:** [Authors from paper context; if absent, state 'ResearchX Academic Working Group']
**Affiliation:** [Department, University / Research Institute from paper context; or 'Department of Artificial Intelligence & Autonomous Systems, ResearchX Academic Platform']
**Correspondence:** [Corresponding author email/contact or 'academic-repository@researchx.org']

---

### ABSTRACT
A comprehensive, high-density 150-250 word academic abstract written as a single cohesive paragraph.
It must explicitly outline:
(1) The underlying research problem and scientific urgency,
(2) The core proposed methodology and architectural framework,
(3) The primary quantitative and qualitative benchmark findings, and
(4) The overarching scientific takeaway and domain significance.
Do NOT use bullet points in the abstract.

**Index Terms**—[Provide 4 to 6 authoritative IEEE Index Terms separated by semicolons, e.g., Deep Learning; Natural Language Processing; Transformer Architecture; Representation Learning]

---

## I. INTRODUCTION
Provide an in-depth academic introduction:
### A. Background & Industrial Motivation
Contextualize the domain challenge, scientific relevance, and why existing systems struggle.
### B. Problem Formulation & Scope
Mathematically or conceptually define the specific obstacle addressed.
### C. Research Objectives & Key Contributions
Enumerate the technical, theoretical, and empirical contributions of this work in clear bullet points.
### D. Paper Organization
A concluding paragraph stating: "The remainder of this paper is organized as follows: Section II surveys related work. Section III formalizes the problem statement and objectives. Section IV presents the proposed methodology and system architecture. Section V outlines the experimental setup and datasets. Section VI analyzes empirical results and discussion. Section VII addresses limitations and research gaps, and Section VIII concludes the paper with future research directions."

## II. RELATED WORK
A rigorous comparative review of prior work and state-of-the-art baselines discussed in the paper:
### A. Theoretical Foundations & Prior Paradigms
Group related works by paradigm or methodology.
### B. Limitations of Existing Approaches
Highlight specific bottlenecks and computational or architectural weaknesses of prior methods.
### C. Differentiating Novelty
Articulate the precise differentiating factors and competitive edge of the current paper.

## III. PROBLEM STATEMENT & OBJECTIVES
Formal mathematical and conceptual specification of the investigated problem:
### A. Mathematical Formulation & System Model
Define symbols, inputs, outputs, and formal objective constraints. Include clean LaTeX equations ($$ ... $$) for optimization objectives.
### B. Research Hypotheses & Design Goals
Detail the operational criteria and expected bounds targeted by the system.

## IV. METHODOLOGY & SYSTEM ARCHITECTURE
An exhaustive, step-by-step technical breakdown of the system:
### A. Architectural Framework Overview
Explain the end-to-end framework, processing modules, and data flow.
### B. Algorithmic Mechanics & Formulation
Detail the core algorithms, loss functions, optimization objectives, or mathematical transformations used.
Format all equations with clean LaTeX notation:
$$L_{{total}} = L_{{task}} + \lambda \Omega(\theta)$$
### C. Feature Extraction & Data Transformation Pipeline
Explain how inputs are ingested, preprocessed, vectorized, and transformed into representations.

## V. EXPERIMENTAL SETUP & DATASETS
Comprehensive documentation of the empirical evaluation protocol:
### A. Benchmark Datasets & Characteristics
Detail dataset names, domains, sample sizes, feature dimensions, and train/validation/test splits. If not specified, state "Not specified in the provided paper."
### B. Baseline Architectures & Comparative Models
Detail baseline methods evaluated against.
### C. Implementation & Hardware Environment
Compute accelerators (GPUs/CPUs), framework (PyTorch/TensorFlow), optimization hyperparameters (learning rate, batch size, epochs), if reported.
### D. Evaluation Metrics
Formal definitions and formulas for metrics employed (Accuracy, Precision, Recall, F1-score, BLEU, ROUGE, Latency, Loss, etc.).

## VI. RESULTS AND DISCUSSION
A detailed empirical evaluation presenting the paper's findings:
### A. Quantitative Benchmark Performance
Include a well-structured **Markdown Comparative Table** summarizing key quantitative findings against baselines.
Format:
TABLE I: COMPARATIVE BENCHMARK EVALUATION
| Model / Configuration | Primary Metric (Accuracy/F1) | Secondary Metric (Latency/PPL) | Notes / Observations |
| :--- | :--- | :--- | :--- |
| [Baseline Model] | [Score] | [Score] | [Observation] |
| [Proposed System] | [Score] | [Score] | [Observation] |

(Preserve every reported number and percentage with absolute fidelity.)

### B. Ablation Studies & Sensitivity Analysis
Detail the effect of individual components, hyperparameter variations, or architectural modules.
### C. Qualitative Analysis & Error Breakdown
Discuss observed error modes, edge cases, and unexpected behaviors observed.

## VII. LIMITATIONS & RESEARCH GAPS
A critical, objective academic appraisal:
### A. Computational Complexity & Scaling Bottlenecks
Memory footprints, training costs, and inference latency constraints.
### B. Threats to Validity & Generalizability
Domain-shift sensitivities, dataset biases, and edge-case failure modes.

## VIII. CONCLUSION & FUTURE WORK
### A. Synthesis of Findings
Summarize whether the empirical evidence successfully validates the core thesis.
### B. Actionable Future Directions
Concrete, actionable research avenues for future investigators (e.g., multimodality, quantization, few-shot adaptation).

## REFERENCES
Numbered IEEE-formatted references corresponding strictly to citations in the paper context:
[1] Author Names, "Paper Title," in *Journal/Conference Name*, vol. X, no. Y, pp. Z, Year.
[2] ...
(Include authentic citations from the context. If full bibliography details are truncated in the context, list available references accurately without inventing fake DOIs or authors.)

==========================================================
TONE AND FORMAT REQUIREMENTS
==========================================================
- Produce formal, third-person IEEE academic English.
- Use Roman numeral section numbering (## I. INTRODUCTION through ## VIII. CONCLUSION & FUTURE WORK, and ## REFERENCES).
- Use lettered subsection headings (### A., ### B., etc.).
- Do NOT include conversational greetings, markdown commentary, or concluding meta-notes.
- Return ONLY the full IEEE manuscript.
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
$$L_{{objective}} = \mathbb{{E}}_{{x \sim p_{{data}}}} [-\log p_\theta(x)]$$
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
        context=context or f"Research Domain Topic: {query}",
        question=question,
    )

    return clean_report_output(raw_output)


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

    return generate_answer(
        context=context,
        question=workspace_question,
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

    return generate_answer(
        context=combined_context,
        question=question,
    )