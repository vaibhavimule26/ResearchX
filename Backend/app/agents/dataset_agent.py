import os
import re
from typing import Optional, List, Dict, Any
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
    """Recommend evidence-grounded, relevant benchmark datasets for
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

STRICT ACCURACY RULES:
1. Analyze ONLY the information explicitly available in the provided paper context.
2. NEVER claim that a dataset was used in the paper unless it is explicitly mentioned in the provided context.
3. If the context does not provide an exact dataset name, do NOT guess the dataset name.
4. Clearly separate:
   - datasets explicitly used in the paper
   - datasets recommended as external alternatives
5. Do NOT generate similarity percentages (e.g., avoid 98%, 95%).
6. Do NOT invent or assume sample sizes, licenses, citations, URLs, benchmark metrics, or loading code.
7. For recommended datasets, recommend only well-known, real datasets relevant to the research task, but do not present unverified metadata as fact.
8. If exact information cannot be verified from the provided context, write: "Not specified in the provided paper context."
9. Do not use information from other uploaded papers when analyzing one paper.
10. Keep the response evidence-grounded, structured, and concise. Do NOT use decorative emoji icons.

Follow this EXACT structure:

### 1. Target Task & Domain Profile
* **Target Domain & Research Area:** Domain of study.
* **Core Task & Objective:** Specific problem being addressed.
* **Input Modality & Data Type:** Modality (e.g., Text, Image, Audio, Tabular, Multimodal).
* **Target Output & Objective:** Ground-truth format or target task goal.

---

### 2. Dataset Usage in Original Paper
*(If analyzing an uploaded paper context, extract all datasets explicitly used. If query-only, state: "N/A — Direct Query Mode (No original paper provided).")*
* **Status:** [Explicitly Used in Paper / Not explicitly mentioned in the provided paper context]
* **Dataset Name:** [Exact dataset name from context, or "Not specified in the provided paper context"]
* **Role in Research:** [How the dataset was utilized, or "Not specified in the provided paper context"]
* **Evidence / Source:** [Direct evidence from the provided context]

---

### 3. Recommended Datasets for This Paper
Recommend 3-4 real and relevant external benchmark datasets that can be used to reproduce, extend, validate, or evaluate the research described in the paper. Do not assign numerical similarity percentages.

* **[Exact Dataset Name]**
  * **Why Recommended:** [Explain specifically why it matches this paper's research problem, domain, or task]
  * **Data Type:** [e.g., Text, Vision/Image, Tabular, Multimodal]
  * **Use for This Paper:** [Explain whether it can be used for training, testing, validation, comparison, reproduction, or extension]
  * **Relation to Original Dataset:** [State whether this is an alternative or complementary dataset to what was used/described]

---

### 4. Implementation & Acquisition Considerations
* **Benchmark Alignment:** Recommended approach for training, validation, or out-of-domain evaluation.
* **Data Preprocessing Considerations:** Key considerations for preprocessing or modality alignment based strictly on standard task requirements.
* **Integrity & Practical Notes:** Licensing, privacy, and domain-specific considerations without fabricating unverified stats.
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
def run_dataset_agent(topic: str, papers: List[Any]) -> List[Dict[str, str]]:
    """Execute the Dataset Recommendation Agent per paper and return
    a structured list of results.
    """
    results = []

    for paper in papers:
        # Support both Pydantic models (paper.title) and standard dictionaries (paper["title"])
        title = getattr(paper, "title", None) or (paper.get("title") if isinstance(paper, dict) else "Untitled Paper")
        summary = (
            getattr(paper, "summary", None)
            or getattr(paper, "abstract", None)
            or (paper.get("summary") or paper.get("abstract") if isinstance(paper, dict) else "Not specified in the paper.")
        )
        published = getattr(paper, "published", None) or (paper.get("published") if isinstance(paper, dict) else "Not specified")

        paper_context = f"""
Title:
{title}

Abstract:
{summary}

Published:
{published}
"""

        question = f"""
Analyze ONLY the provided paper context.

Return the answer in EXACTLY this format:

## 1. Dataset Used in Original Paper

First determine whether the paper explicitly mentions using a dataset.

If a dataset is explicitly mentioned in the provided paper context, write:

- **Dataset Name:** Exact dataset name
- **Status:** Explicitly Used in Paper
- **Purpose:** Explain how the dataset was used
- **Evidence:** Mention the exact evidence available in the provided context

If NO dataset is explicitly mentioned in the provided paper context, write:

- **Status:** Not explicitly mentioned in the provided paper context.
- Do NOT guess or invent a dataset used by the paper.
- Do NOT say a dataset was used merely because it is relevant to the topic.

## 2. Recommended Datasets for This Paper

Recommend 3 to 4 REAL and relevant datasets that can be used to reproduce,
extend, or evaluate the research described in THIS paper.

For each recommended dataset use:

### Dataset Name

- **Why Recommended:** Explain specifically why it matches this paper's research problem.
- **Data Type:** Text / Image / Audio / Tabular / Multimodal etc.
- **Use for This Paper:** Explain whether it can be used for training, testing,
  validation, comparison, reproduction, or extension.
- **Relation to Original Dataset:** If the paper used a dataset, clearly state
  whether this is an alternative or complementary dataset.

STRICT RULES:

1. Analyze this paper independently. Do not use information from other papers.
2. NEVER claim a dataset was used unless explicitly stated in the provided context.
3. If the context only says "Kaggle dataset", write exactly what is supported.
   Do not invent the exact dataset name unless the paper provides it.
4. Recommended datasets must be clearly separated from datasets actually used
   in the paper.
5. Do not include generic unrelated recommendations.
6. Do not generate similarity percentages such as 98% or 95%.
7. Do not invent sample sizes, licenses, citations, URLs, metrics, or loading code.
8. Keep the answer concise and relevant.
"""

        try:
            result = generate_answer(
                context=paper_context,
                question=question
            )

            if not result or len(result.strip()) < 50:
                result = "Unable to generate dataset analysis for this paper."

        except Exception as e:
            print(f"[Dataset Agent Error for '{title}']: {e}")
            result = "Unable to generate dataset analysis for this paper."

        results.append({
            "paper_name": title,
            "result": result.strip()
        })

    return results