import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.agents.coordinator import load_context_for_paper
from app.llm.gemini import generate_answer
from app.llm.multi_api_router import (
    call_cohere_api,
    call_mistral_api,
    call_groq_api,
    call_openrouter_api,
)


def clean_experiment_output(text: str) -> str:
    """
    Clean LLM experiment analysis output while preserving valid Markdown tables, headers, and lists.
    """
    if not text:
        return ""

    result = text.strip()

    # Strip code block fences if any
    result = re.sub(
        r"^```(?:text|markdown|plain)?\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )
    result = re.sub(r"\s*```$", "", result)

    # Handle literal escaped characters
    result = (
        result.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\r", "\n")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\x00", "")
        .replace("\ufffd", "—")
    )

    # Ensure clean blank line before markdown headers
    result = re.sub(r'([^\n])\n(#{1,6}\s+)', r'\1\n\n\2', result)

    # Normalize excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


# ==========================================================
# SINGLE PAPER EXPERIMENT PLANNING AGENT
# ==========================================================

def plan_experiments(
    context: Optional[str] = None,
    paper_name: Optional[str] = None,
    query: Optional[str] = None,
    pdf_url: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Generate an evidence-grounded, comprehensive experiment analysis and validation protocol
    for one research paper based specifically on its actual content, methodology, and reported results.
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

    # If context is not passed directly, retrieve it from the uploaded paper
    if not content or len(content.strip()) < 100:
        retrieved = load_context_for_paper(
            paper_name=doc_title,
            query=query or "experimental setup methodology benchmarks results",
            pdf_url=pdf_url,
        )
        if retrieved and len(retrieved.strip()) >= 100:
            content = retrieved

    if not content or len(content.strip()) < 50:
        return (
            "Insufficient research paper context available to design accurate experiments. "
            "Please verify the uploaded document."
        )

    paper_context = content[:32000]

    prompt = f"""You are ResearchX, an expert academic research intelligence assistant specializing in rigorous empirical experimental design and validation methodology.
Analyze the provided research paper context to extract the authentic experimental setup, benchmark results, and formulate an evidence-grounded experimental reproduction and extension plan.

PAPER TITLE: {doc_title}
{f'RESEARCH FOCUS / QUERY: {query.strip()}' if query and query.strip().lower() not in ['experiments', 'experiment', 'experiment_recommendation', 'summary', 'gaps'] else ''}

STRICT EVIDENCE DIRECTIVES:
1. Extract and summarize the ORIGINAL experimental setup and results STRICTLY from the provided paper context.
2. Differentiate clearly between:
   - What the authors actually implemented, tested, and reported in the paper.
   - Any missing, omitted, or unstated parameters (e.g. learning rate, random seeds, hardware). Label them as "Not reported in the paper text".
   - Your recommended replication, ablation, and extension protocols. Clearly label these as "Recommended".
3. Do NOT fabricate numbers, baseline scores, dataset sizes, or models that are not present in the paper.
4. Output in clean, professional Markdown with structured headings, bullet points, and tables.

FORMAT YOUR RESPONSE USING THESE EXACT SECTIONS:

### 1. Core Experimental Objective & Hypotheses
- **Research Problem & Evaluation Aim:** The primary technical claim or hypothesis the authors set out to empirically validate.
- **Experimental Target:** What specific performance, efficiency, or qualitative advantage the experiments are designed to demonstrate.

### 2. Original Paper Experimental Setup
- **Benchmark Datasets & Data Sources:** Specific datasets used (names, domains, sample counts, train/val/test splits, or data collection protocols as reported in the paper).
- **Model Architectures & Baselines:** Proposed model/method architecture along with the exact baseline models or competitor techniques compared against.
- **Input & Output Specifications:** Data inputs, feature representations, and target outputs/predictions.
- **Hyperparameters & Training Protocol:** Optimizers, learning rates, epochs/iterations, batch size, loss functions, and hardware specifications (or state "Not reported in the paper text" if omitted).
- **Evaluation Metrics:** Quantitative and qualitative metrics used to measure performance (e.g. Accuracy, F1 Score, AUROC, BLEU, ROUGE, Latency, Peak VRAM).

### 3. Reported Empirical Results & Quantitative Findings
- **Key Benchmark Results:** Primary quantitative scores, accuracy/efficiency numbers, and error rates reported by the authors.
- **Comparative Findings vs. Baselines:** How the proposed method compared quantitatively against the baselines (e.g., percentage improvements, margin of gain, or trade-offs).
- **Key Validation Insights:** Main takeaways and conclusions derived directly from the paper's experiments.

### 4. Experimental Limitations & Missing Execution Details
- **Author-Acknowledged Limitations:** Empirical constraints, failure cases, or dataset scope limitations admitted by the authors.
- **Missing / Omitted Details:** Critical hyperparameters, initialization details, random seed variance, or hardware constraints omitted in the text that could hinder direct reproduction.

### 5. Recommended Reproduction & Extension Protocol
- **Recommended Reproduction Steps:** 3-4 concrete, sequential steps for an independent researcher to replicate the paper's core findings.
- **Recommended Contemporary Baselines:** Relevant newer or standard benchmark baselines to test against for comprehensive validation.
- **Recommended Ablation & Stress Testing:** Specific component ablation tests, sensitivity checks, or out-of-distribution/stress tests to verify robustness.

### 6. Experimental Design & Validation Matrix
| Phase | Experimental Objective | Proposed Setup vs. Baseline | Target Evaluation Metric | Expected Validation Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1. Baseline Replication** | Verify authors' reported benchmark scores | Proposed model vs primary reported baseline | Primary accuracy/performance metrics | Matches or closely approximates reported numbers within margin |
| **2. Component Ablation** | Isolate contribution of key modules | Full architecture vs ablated variants | Target performance & efficiency metrics | Identifies key drivers of empirical performance gains |
| **3. Stress & Robustness** | Validate out-of-distribution & noise resilience | Perturbed/OOD test data vs clean benchmark | Robustness & degradation rate | Evaluates generalization boundaries and failure modes |
"""

    raw_output = ""

    # Strategy 1: Cohere Command-R (Exceptional for factual grounding & structured reasoning)
    try:
        raw_output = call_cohere_api(prompt=prompt, context=paper_context)
    except Exception as e:
        print(f"[Experiment Agent Cohere Error]: {e}")

    # Strategy 2: Mistral Fallback
    if (
        not raw_output
        or not raw_output.strip()
        or "failed" in raw_output.lower()
        or "no llm api" in raw_output.lower()
    ):
        try:
            print("[Experiment Agent] Cohere unavailable, falling back to Mistral...")
            raw_output = call_mistral_api(prompt=prompt, context=paper_context)
        except Exception as e:
            print(f"[Experiment Agent Mistral Error]: {e}")

    # Strategy 3: Groq / OpenRouter Fallback
    if (
        not raw_output
        or not raw_output.strip()
        or "failed" in raw_output.lower()
        or "no llm api" in raw_output.lower()
    ):
        try:
            print("[Experiment Agent] Falling back to Groq...")
            raw_output = call_groq_api(prompt=prompt, context=paper_context)
        except Exception as e:
            print(f"[Experiment Agent Groq Error]: {e}")

    # Strategy 4: OpenRouter Fallback
    if (
        not raw_output
        or not raw_output.strip()
        or "failed" in raw_output.lower()
        or "no llm api" in raw_output.lower()
    ):
        try:
            print("[Experiment Agent] Falling back to OpenRouter...")
            raw_output = call_openrouter_api(prompt=prompt, context=paper_context)
        except Exception as e:
            print(f"[Experiment Agent OpenRouter Error]: {e}")

    # Strategy 5: Gemini Fallback
    if (
        not raw_output
        or not raw_output.strip()
        or "failed" in raw_output.lower()
        or "no llm api" in raw_output.lower()
    ):
        try:
            print("[Experiment Agent] Falling back to Gemini...")
            raw_output = generate_answer(
                context=paper_context,
                question=prompt,
            )
        except Exception as e:
            print(f"[Experiment Agent Gemini Error]: {e}")

    cleaned = clean_experiment_output(raw_output)

    if not cleaned:
        return "Unable to generate experimental analysis for the provided paper context."

    return cleaned


# ==========================================================
# MULTI-PAPER WORKSPACE EXPERIMENT AGENT
# ==========================================================

def run_experiment_agent(
    topic: str,
    papers: List[Any],
) -> List[Dict[str, str]]:
    """
    Generate concise, high-impact experiment recommendations and evaluation techniques
    for each selected research paper.
    """
    if not papers:
        return [{
            "paper_name": "Experiments",
            "result": "No research papers were provided."
        }]

    results = []
    print(f"[Experiment Agent] Processing {len(papers)} papers...")

    for idx, paper in enumerate(papers, start=1):
        if isinstance(paper, dict):
            title = paper.get("title") or paper.get("paper_name") or f"Paper {idx}"
            summary = (
                paper.get("abstract")
                or paper.get("summary")
                or paper.get("why_chosen")
                or paper.get("key_contribution")
                or f"Research investigation on {topic} focusing on {title}."
            )
            venue = paper.get("venue") or ""
            published = paper.get("published") or "Not specified"
            pdf_url = paper.get("pdf_url") or paper.get("url")
        elif isinstance(paper, str):
            title = paper
            summary = f"Research investigation on {topic} focusing on {title}."
            venue = ""
            published = "Not specified"
            pdf_url = None
        else:
            title = getattr(paper, "title", None) or getattr(paper, "paper_name", None) or f"Paper {idx}"
            summary = (
                getattr(paper, "abstract", None)
                or getattr(paper, "summary", None)
                or getattr(paper, "why_chosen", None)
                or getattr(paper, "key_contribution", None)
                or f"Research investigation on {topic} focusing on {title}."
            )
            venue = getattr(paper, "venue", "")
            published = getattr(paper, "published", "Not specified")
            pdf_url = getattr(paper, "pdf_url", None) or getattr(paper, "url", None)

        print(f"[Experiment Agent] ({idx}/{len(papers)}) PAPER: {title}")

        # Retrieve actual paper evidence (for local files, load text; for online papers, use abstract)
        paper_context = ""
        if title.lower().endswith(".pdf"):
            try:
                paper_context = load_context_for_paper(
                    paper_name=title,
                    query=topic or "experiments methodology benchmarks results",
                    pdf_url=pdf_url,
                )
            except Exception as e:
                print(f"[Experiment Agent Context Error - {title}]: {e}")
                paper_context = ""

        # Rich context fallback using paper abstract & metadata
        if not paper_context or len(paper_context.strip()) < 100:
            paper_context = f"""Title: {title}
Abstract / Focus: {summary}
Venue / Source: {venue}
Published: {published}"""

        question = f"""You are the Senior Experimental Design & Evaluation Architect at ResearchX.
Identify and recommend appropriate experiments and evaluation techniques for this research paper based on its research problem, methodology, and objectives.

Paper Title: {title}
Research Topic: {topic}

Use this EXACT format:

### 1. Core Validation Objective
- **Hypothesis:** 1 crisp sentence stating the primary testable claim and expected performance gain.
- **Key Metrics:** Primary evaluation metrics (e.g. Accuracy, F1 Score, Latency/Throughput, BLEU/ROUGE).

### 2. Recommended Experiment & Validation Matrix
| Phase | Objective | Proposed Setup vs Baseline | Validation Metric | Target Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **1. Comparative Benchmark** | Primary comparative evaluation | Proposed model vs standard baselines | Primary task metrics | Statistically significant improvement |
| **2. Ablation & Efficiency** | Component contribution & speed | Proposed system with/without key components | Latency (ms) / Memory (MB) | Quantifies efficiency-accuracy trade-off |

### 3. Execution Notes
- **Data & Protocol:** Benchmark split (e.g. 70/15/15) with standard task preprocessing.
- **Validation:** 5-fold cross-validation or paired significance testing under controlled hyperparameters.
"""

        result = ""
        # Multi-API cascade
        try:
            result = call_cohere_api(prompt=question, context=paper_context)
        except Exception as e:
            print(f"[Experiment Agent Cohere Error for '{title}']: {e}")

        if not result or len(result.strip()) < 50 or "failed" in result.lower() or "no llm api" in result.lower():
            try:
                result = call_mistral_api(prompt=question, context=paper_context)
            except Exception as e:
                print(f"[Experiment Agent Mistral Error for '{title}']: {e}")

        if not result or len(result.strip()) < 50 or "failed" in result.lower() or "no llm api" in result.lower():
            try:
                result = call_groq_api(prompt=question, context=paper_context)
            except Exception as e:
                print(f"[Experiment Agent Groq Error for '{title}']: {e}")

        if not result or len(result.strip()) < 50 or "failed" in result.lower() or "no llm api" in result.lower():
            try:
                result = generate_answer(context=paper_context, question=question)
            except Exception as e:
                print(f"[Experiment Agent Gemini Error for '{title}']: {e}")

        results.append({
            "paper_name": title,
            "result": clean_experiment_output(result) if result else "Unable to generate experiment recommendation for this paper."
        })

    return results


# ==========================================================
# BACKWARD-COMPATIBLE FUNCTION ALIASES
# ==========================================================

recommend_experiments = plan_experiments
run_experiments = run_experiment_agent
design_experiments = plan_experiments