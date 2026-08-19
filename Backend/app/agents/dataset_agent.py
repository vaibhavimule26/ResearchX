import os
import re
from typing import Optional
from app.llm.gemini import generate_answer
from app.llm.multi_api_router import (
    call_cohere_api,
    call_groq_api,
    call_mistral_api,
)


# ==========================================================
# High-Similarity Benchmark Dataset Recommendation Agent
# ==========================================================
def recommend_datasets(context: str = "", query: str = "") -> str:
    """Recommend evidence-grounded, highly similar benchmark datasets for
    extending, validating, or reproducing research based on a paper context
    or direct user query.
    """
    clean_context = (context or "").strip()
    clean_query = (query or "").strip()

    if not clean_context and not clean_query:
        return (
            "Unable to recommend datasets because neither a research paper context "
            "nor a user query was provided. Please upload a PDF or enter a research topic."
        )

    # Determine execution modality
    has_paper = len(clean_context) > 50
    has_query = len(clean_query) > 0

    if has_paper and has_query:
        target_description = f"Research Query: '{clean_query}'\nPaper Context Provided: Yes ({len(clean_context)} characters)"
    elif has_paper:
        target_description = "Uploaded Research Paper (PDF Context)"
    else:
        target_description = f"User Research Topic / Query: '{clean_query}'"

    prompt = f"""
You are the Lead Research Dataset Specialist and AI Benchmark Architect at ResearchX.

Your objective is to provide a rigorous, highly accurate, and standardized Dataset Recommendation Report for:
{target_description}

CRITICAL ACCURACY & RELEVANCE RULES:
1. ONLY recommend REAL, authoritative, peer-reviewed, and publicly accessible benchmark datasets with HIGH SIMILARITY (>90% alignment) to the input domain, task, and modality.
2. For EVERY dataset, you MUST provide a deep technical "Selection Reason & Alignment Justification" explaining WHY this specific dataset is selected (domain fit, task compatibility, ground-truth quality, and baseline comparability).
3. Do NOT recommend generic, irrelevant, or hallucinated datasets. Ensure exact dataset names, standard metrics, and real open-access/academic licenses.
4. If a paper context is provided, distinguish datasets explicitly used in the paper from recommended external datasets.
5. If only a user query is provided, analyze the core task and provide the top 3-4 authoritative benchmark datasets.
6. Output in clean, standardized GitHub-Flavored Markdown. Do NOT use decorative emoji icons.

Follow this EXACT structure:

### 1. Target Task & Domain Profile
* **Target Domain & Research Area:** Domain of study.
* **Core Task & Objective:** Specific problem being addressed.
* **Input Modality & Data Schema:** Modality (e.g., Medical Imaging DICOM, NLP Text, Audio WAV, Multi-modal Vision-Language, Tabular Time-Series).
* **Target Output & Evaluation Standards:** Ground-truth format and key metrics (e.g., AUROC, F1-score, BLEU, mAP, Accuracy).

---

### 2. Dataset Usage in Original Paper
*(If analyzing an uploaded paper context, extract all datasets explicitly used. If query-only, state: "N/A — Direct Query Mode (No original paper provided).")*
* **[Dataset Name]**
  * **Status:** Explicitly Used in Paper / Baseline Benchmark
  * **Role in Research:** How the dataset was utilized in the architecture/experiments.
  * **Data Modality & Scale:** Format and sample size.
  * **Evidence / Source:** Citation or evidence from the paper context.

---

### 3. Highly Similar Recommended External Datasets
Recommend 2-4 authoritative external benchmark datasets with >90% similarity:

* **[Exact Dataset Name]**
  * **Similarity & Alignment Level:** [e.g., 98% — Highly Similar / Direct Domain Match]
  * **Modality & Format:** [e.g., DICOM Images, JSON QA Pairs, Parquet, CSV]
  * **Scale & Size:** [e.g., 112,120 annotated samples, 45 GB]
  * **Selection Reason & Technical Justification:** [Comprehensive 2-4 sentence explanation of WHY this specific dataset is recommended for this research query or paper, detailing task alignment, baseline comparison capability, and ground-truth reliability.]
  * **Ground-Truth & Annotation Quality:** [e.g., Human expert verified, double-blind clinical annotation, consensus labels]
  * **Key Benchmark Evaluation Metrics:** [e.g., AUROC, F1-Score, Top-1 Accuracy, Exact Match]
  * **License & Access:** [e.g., CC BY 4.0 / PhysioNet Credentialed / MIT Open Source / HuggingFace Dataset]
  * **Formal Citation:** [Standard Academic Citation: Authors, Title, Venue/Repository, Year]
  * **Direct Loading Snippet:** [e.g., `from datasets import load_dataset; ds = load_dataset('...')` or torchvision/kaggle code]

---

### 4. Dataset Verification & Comparison Matrix

Output a standard GitHub-Flavored Markdown table with exactly 7 columns:

| Dataset | Modality & Format | Scale & Size | Similarity Match | Selection Reason | License & Access | Primary Benchmark Metric |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [Dataset 1] | [Modality] | [Size] | [e.g. 98% Direct] | [Summary of selection rationale] | [License] | [Metric] |
| [Dataset 2] | [Modality] | [Size] | [e.g. 95% High] | [Summary of selection rationale] | [License] | [Metric] |
| [Dataset 3] | [Modality] | [Size] | [e.g. 92% High] | [Summary of selection rationale] | [License] | [Metric] |

---

### 5. Implementation & Acquisition Protocol
* **Optimal Benchmark Stack:** Recommended split between primary training, validation, and out-of-domain generalization testing.
* **Data Ingestion & Preprocessing Pipeline:** Step-by-step guidance on normalization, tokenization, or augmentations required.
* **Reproducibility & Integrity Notes:** Licensing compliance, privacy/IRB considerations, and AI-detection/synthetic artifact audit.
"""

    combined_input = ""
    if clean_context and clean_query:
        combined_input = f"USER QUERY:\n{clean_query}\n\nRESEARCH PAPER CONTEXT:\n{clean_context[:22000]}"
    elif clean_context:
        combined_input = f"RESEARCH PAPER CONTEXT:\n{clean_context[:22000]}"
    else:
        combined_input = f"USER RESEARCH QUERY:\n{clean_query}"

    # Multi-API Execution Pipeline with Resilient Fallback
    # 1. Primary: Gemini 3.6 Flash
    try:
        gemini_res = generate_answer(
            context=combined_input,
            question=prompt,
        )
        if gemini_res and len(gemini_res.strip()) > 100 and not gemini_res.startswith("Gemini returned"):
            return gemini_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Gemini Fallback]: {e}")

    # 2. Secondary: Cohere Command-R
    try:
        cohere_res = call_cohere_api(
            prompt=prompt,
            context=combined_input[:12000],
        )
        if cohere_res and len(cohere_res.strip()) > 100 and not cohere_res.startswith("Cohere"):
            return cohere_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Cohere Fallback]: {e}")

    # 3. Tertiary: Groq / Qwen / Compound
    try:
        groq_res = call_groq_api(
            prompt=prompt,
            context=combined_input[:12000],
        )
        if groq_res and len(groq_res.strip()) > 100:
            return groq_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Groq Fallback]: {e}")

    # 4. Quaternary: Mistral
    try:
        mistral_res = call_mistral_api(
            prompt=prompt,
            context=combined_input[:12000],
        )
        if mistral_res and len(mistral_res.strip()) > 100:
            return mistral_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Mistral Fallback]: {e}")

    return (
        "Dataset Recommendation Agent encountered an issue with language model endpoints. "
        "Please check your API keys or retry."
    )


# ==========================================================
# Multi-Paper Workspace Dataset Agent
# ==========================================================
def run_dataset_agent(topic: str, papers) -> str:
    """Execute the Dataset Recommendation Agent
    for all selected papers in a workspace.
    """
    print("Running Dataset Recommendation Agent...")
    context = "\n\n".join(
        [
            f"""
Title: {getattr(paper, 'title', 'Untitled')}
Authors: {", ".join(getattr(paper, 'authors', [])) if isinstance(getattr(paper, 'authors', None), list) else getattr(paper, 'authors', '')}
Summary: {getattr(paper, 'summary', '')}
Published: {getattr(paper, 'published', '')}
"""
            for paper in papers
        ]
    )
    return recommend_datasets(context=context, query=topic)