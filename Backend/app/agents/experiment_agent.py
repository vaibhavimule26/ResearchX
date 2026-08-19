from app.llm.gemini import generate_answer


# ==========================================================
# Single Paper Experiment Planning Agent
# ==========================================================
def plan_experiments(context: str) -> str:
    """Generate a step-by-step experimental design, reproduction protocol,
    and benchmarking setup based on the research paper context.
    """
    if not context or not context.strip():
        return (
            "Unable to generate experiment protocol because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper context as a senior AI systems researcher.

Design a comprehensive, rigorous Experimental Replication and Validation Protocol.

Output your response using this exact Markdown structure:

### 1. Experimental Objectives & Hypotheses
* **Primary Objective:** Core capability or benchmark being validated.
* **Core Hypotheses:** 2-3 formal testable hypotheses addressing accuracy, latency, and resource constraints.

---

### 2. Baseline Models & Comparative Benchmarks
* **Selected Baselines:** List standard and state-of-the-art models used for comparative evaluation.
* **Comparison Setup:** Specific parameters, prompt templates, and ablation configurations.

---

### 3. Evaluation Metrics & Success Criteria
* **Quantitative Metrics:** Specific retrieval and generation metrics (e.g., Hit Rate@K, MRR, BLEU-4, ROUGE-L, Perplexity, Inference Latency).
* **Validation Thresholds:** Concrete performance targets required to confirm successful reproduction.

---

### 4. Compute, Environment & Resource Requirements
* **Hardware Setup:** CPU/GPU specifications, RAM, and edge device requirements.
* **Software Frameworks:** Python versions, core libraries (e.g., PyTorch, FAISS, llama.cpp, Transformers), and quantizing schemes.

---

### 5. Step-by-Step Execution Protocol
1. **Data Ingestion & Indexing:** Preprocessing, embedding extraction, and index build steps.
2. **Model Quantization & Setup:** Loading local weights, memory allocation, and context limits.
3. **Execution & Metric Logging:** Running automated benchmark scripts and gathering latency/accuracy telemetry.

CRITICAL INSTRUCTIONS:
- Ground details in the specific paper context (extract exact hardware specs, dataset splits, and metrics where present).
- Keep formatting clean using standard Markdown headings (###), bullet points, and horizontal rules (---).
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Multi-Paper Workspace Experiment Agent
# ==========================================================
def run_experiment_agent(topic: str, papers) -> str:
    """Execute the Experiment Agent for all selected papers in a workspace."""
    print("Running Experiment Recommendation Agent...")
    context = "\n\n".join(
        [
            f"""
Title: {getattr(paper, 'title', 'Untitled')}
Authors: {", ".join(getattr(paper, 'authors', []))}
Summary: {getattr(paper, 'summary', '')}
Published: {getattr(paper, 'published', '')}
"""
            for paper in papers
        ]
    )
    return plan_experiments(context)


# ==========================================================
# Backward-Compatible Function Aliases
# ==========================================================
recommend_experiments = plan_experiments
run_experiments = run_experiment_agent