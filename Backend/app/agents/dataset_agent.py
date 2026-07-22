from app.llm.gemini import generate_answer


def recommend_datasets(context: str) -> str:
    """
    Recommend evidence-grounded datasets for extending,
    validating, or reproducing the selected research paper.
    """

    if not context or not context.strip():
        return (
            "Unable to recommend datasets because "
            "no research paper context was provided."
        )

    question = """
Analyze the provided research paper context as an expert
research dataset specialist.

Produce a detailed Dataset Recommendation Report with exactly
these sections:

1. Paper Data Requirements
- Identify the type of data required by the paper.
- Explain the task, domain, input format, output labels,
  modalities, and evaluation needs when supported by context.

2. Datasets Explicitly Mentioned in the Paper
- List datasets explicitly named in the provided paper context.
- For each dataset explain how it is used.
- Do not invent dataset names.
- If no dataset is explicitly mentioned, clearly state that.

3. Recommended Public Datasets
For each suitable dataset provide:
- Dataset Name
- Domain
- Why It Is Suitable
- Possible Use Case
- Expected Data Type or Modality
- Access Source or Platform, if confidently known

4. Dataset Comparison
Compare the recommended datasets using:
- relevance to the paper
- scale
- task compatibility
- likely strengths
- likely limitations

5. Best Dataset Recommendation
- Select the single best dataset or dataset combination.
- Explain why it is the strongest match.
- Suggest how it could be used in a concrete experiment.

Important rules:
- Base the analysis on the provided research paper context.
- Never claim that a dataset was used in the paper unless the
  provided context explicitly supports that claim.
- Clearly distinguish:
  a) datasets explicitly mentioned in the paper
  b) external datasets recommended by you
- Do not invent dataset names, benchmark statistics, URLs,
  licenses, sizes, or access conditions.
- If exact information is uncertain, say so clearly.
- Prefer well-established public research datasets when a
  recommendation can be made confidently.
- Be specific to this paper.
- Avoid generic recommendations.
- Give a detailed answer.
"""

    return generate_answer(
        context=context,
        question=question,
    )
    
    # ==========================================================
# Workspace Dataset Agent
# ==========================================================
def run_dataset_agent(topic: str, papers) -> str:
    """
    Execute the Dataset Recommendation Agent
    for all selected papers.
    """

    print("Running Dataset Recommendation Agent...")

    context = "\n\n".join(
        [
            f"""
Title: {paper.title}
Authors: {", ".join(paper.authors)}
Summary: {paper.summary}
Published: {paper.published}
"""
            for paper in papers
        ]
    )

    return recommend_datasets(context)