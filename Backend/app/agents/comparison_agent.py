from app.llm.gemini import generate_answer


def compare_papers(context):

    prompt = f"""
You are an expert AI Research Assistant.

You have been provided with multiple uploaded research papers.

Your task is to compare them.

Generate a detailed comparison using the following format.

# Research Paper Comparison

## 1. Paper Titles

List all uploaded paper titles.

## 2. Main Objectives

Compare the objective of each paper.

## 3. Methodology

Compare the methodologies.

## 4. Datasets Used

Compare the datasets.

## 5. Models / Algorithms

Compare the proposed models or algorithms.

## 6. Key Contributions

Compare the contributions.

## 7. Experimental Results

Compare the experimental findings.

## 8. Strengths

Mention strengths of each paper.

## 9. Weaknesses

Mention weaknesses of each paper.

## 10. Future Work

Compare future work.

## 11. Final Conclusion

Summarize similarities and differences.

If only one paper is available, clearly state that comparison requires at least two uploaded research papers.

Research Papers:

{context}
"""

    return generate_answer(prompt, "")