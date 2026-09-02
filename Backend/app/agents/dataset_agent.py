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
    """Recommend evidence-grounded, highly relevant datasets for
    each research paper based on the topic, problem statement, objectives,
    and experimental requirements.
    """
    clean_context = (context or "").strip()
    clean_query = (query or "").strip()

    if not clean_context and not clean_query:
        return (
            "Unable to recommend datasets because neither a research paper context "
            "nor a user query was provided. Please upload a PDF or enter a research topic."
        )

    prompt = f"""
You are the Lead Research Dataset Specialist and AI Benchmark Architect at ResearchX.

MOTIVE & OBJECTIVE:
Identify and recommend relevant datasets for the research based on the research topic, problem statement, objectives, and experimental requirements. Help the researcher determine what data can be used to conduct, validate, and support the research.

Research Topic: {clean_query or 'Academic Research Topic'}

Analyze the provided paper context thoroughly and generate a comprehensive Dataset Recommendation Report using EXACTLY this structure:

### 1. Problem Statement & Data Requirements
- **Research Problem & Objectives:** Core problem being addressed and the primary objectives of the research.
- **Required Data Modality:** Text, Vision/Image, Tabular, Audio, Multimodal, Graph, Time-Series, etc.
- **Data Characteristics Needed:** Scale, annotations, label granularity, feature distribution, or domain specifics needed to conduct and support the investigation.

---

### 2. Recommended Datasets Matrix

| Dataset Name | Domain / Modality | Target Task / Use Case | Dataset Characteristics & Availability | Why Recommended for This Research |
| :--- | :--- | :--- | :--- | :--- |

(Provide 3-4 real, widely established academic benchmark datasets that can be used to train, evaluate, replicate, or extend this research. Fill every cell concisely and factually.)

---

### 3. Dataset Acquisition & Experimental Protocol
- **Primary Training & Evaluation Dataset:** The best-fit primary dataset and recommended train/test splits.
- **Cross-Domain & Robustness Datasets:** Alternative or complementary datasets to test generalization.
- **Preprocessing & Implementation Guidelines:** Essential preprocessing steps, tokenization/normalization, feature extraction, or data augmentation strategies needed to prepare the data for experiments.
"""

    combined_input = ""
    if clean_context and clean_query:
        combined_input = f"USER QUERY:\n{clean_query}\n\nRESEARCH PAPER CONTEXT:\n{clean_context[:22000]}"
    elif clean_context:
        combined_input = f"RESEARCH PAPER CONTEXT:\n{clean_context[:22000]}"
    else:
        combined_input = f"USER RESEARCH QUERY:\n{clean_query}"

    try:
        gemini_res = generate_answer(
            context=combined_input,
            question=prompt,
        )
        if gemini_res and len(gemini_res.strip()) > 100 and not gemini_res.startswith("Gemini returned"):
            return gemini_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Gemini Fallback]: {e}")

    try:
        cohere_res = call_cohere_api(
            prompt=prompt,
            context=combined_input[:12000],
        )
        if cohere_res and len(cohere_res.strip()) > 100 and not cohere_res.startswith("Cohere"):
            return cohere_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Cohere Fallback]: {e}")

    try:
        groq_res = call_groq_api(
            prompt=prompt,
            context=combined_input[:12000],
        )
        if groq_res and len(groq_res.strip()) > 100:
            return groq_res.strip()
    except Exception as e:
        print(f"[Dataset Agent - Groq Fallback]: {e}")

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
    a structured list of results recommending relevant datasets for each paper.
    """
    results = []

    for paper in papers:
        # Support both Pydantic models (paper.title) and standard dictionaries (paper["title"])
        title = getattr(paper, "title", None) or (paper.get("title") if isinstance(paper, dict) else "Untitled Paper")
        summary = (
            getattr(paper, "summary", None)
            or getattr(paper, "abstract", None)
            or getattr(paper, "why_chosen", None)
            or getattr(paper, "key_contribution", None)
            or (paper.get("summary") or paper.get("abstract") or paper.get("why_chosen") or paper.get("key_contribution") if isinstance(paper, dict) else f"Research paper on {topic} focusing on {title}.")
        )
        venue = getattr(paper, "venue", "") or (paper.get("venue") if isinstance(paper, dict) else "")
        published = getattr(paper, "published", None) or (paper.get("published") if isinstance(paper, dict) else "Not specified")

        paper_context = f"""
Title:
{title}

Abstract / Focus:
{summary}

Venue / Source:
{venue}

Published:
{published}
"""

        question = f"""
You are the Lead Research Dataset Specialist and AI Benchmark Architect at ResearchX.

MOTIVE & OBJECTIVE:
Identify and recommend relevant datasets for this research paper based on the research topic, problem statement, objectives, and experimental requirements. Help the researcher determine what data can be used to conduct and support the research.

Paper Title: {title}
Research Topic: {topic}

Generate a clear, authoritative, and evidence-grounded dataset recommendation report for this paper:

### 1. Problem Statement & Data Requirements
- **Core Research Problem:** The specific challenge or objective addressed by {title}.
- **Required Data Modality & Characteristics:** Modality (text, vision, audio, tabular, multimodal), required annotations, dataset scale, and distribution needed to conduct the research.

---

### 2. Recommended Datasets Table

| Dataset Name | Domain / Modality | Target Task / Use Case | Dataset Characteristics | Why Recommended for This Research |
| :--- | :--- | :--- | :--- | :--- |

(Provide 3-4 real, widely established academic benchmark datasets that can be used to train, evaluate, reproduce, or extend the proposed approach. Fill each cell concisely and factually.)

---

### 3. Implementation & Validation Strategy
- **Benchmark Split Protocol:** Standard training, validation, and testing split recommendations.
- **Data Preprocessing & Augmentation:** Key preprocessing steps and normalization required for effective model training and evaluation.
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

    return results