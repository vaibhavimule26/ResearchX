from app.llm.gemini import generate_answer


def recommend_datasets(context):
    """
    Recommend datasets for the uploaded research paper.
    """

    prompt = f"""
You are an expert AI Research Assistant.

Analyze the following research paper and recommend suitable datasets.

For each dataset provide:

1. Dataset Name
2. Why it is suitable
3. Link if commonly available
4. Possible use cases

Research Paper:

{context}
"""

    return generate_answer(prompt, "")