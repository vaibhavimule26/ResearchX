from app.llm.gemini import generate_answer


def generate_presentation(context: str) -> str:
    """
    Generate a professional IEEE-style PowerPoint presentation
    from the uploaded research paper.
    """

    if not context or not context.strip():
        return "No research paper context was provided."

    question = """
You are a senior IEEE conference presentation designer.

Analyze ONLY the uploaded research paper and generate a professional conference presentation.

Your output MUST follow this format EXACTLY.

======================================================

### Slide 1
**Slide Title:** Paper Title

**Bullet Points**
- Paper title
- Authors
- Organization (if available)
- Conference / Journal (if available)

**Speaker Notes**
Briefly introduce the paper.

======================================================

### Slide 2
**Slide Title:** Problem Statement

**Bullet Points**
- Main research problem
- Motivation
- Why it is important
- Existing challenge

**Speaker Notes**
Explain the motivation.

======================================================

### Slide 3
**Slide Title:** Objectives

**Bullet Points**
- Primary objective
- Secondary objective
- Expected outcome
- Research goal

**Speaker Notes**
Explain the objectives.

======================================================

### Slide 4
**Slide Title:** Related Work

**Bullet Points**
- Existing methods
- Previous approaches
- Limitations
- Comparison

**Speaker Notes**
Summarize previous work.

======================================================

### Slide 5
**Slide Title:** Proposed Methodology

**Bullet Points**
- Proposed approach
- Workflow
- Key algorithm
- Core idea

**Speaker Notes**
Explain the methodology.

======================================================

### Slide 6
**Slide Title:** Dataset

**Bullet Points**
- Dataset used
- Source
- Size
- Important characteristics

**Speaker Notes**
Explain the dataset.

======================================================

### Slide 7
**Slide Title:** Experimental Setup

**Bullet Points**
- Hardware
- Software
- Evaluation metrics
- Baselines

**Speaker Notes**
Explain the experiments.

======================================================

### Slide 8
**Slide Title:** Results

**Bullet Points**
- Main findings
- Performance
- Improvements
- Observations

**Speaker Notes**
Explain the results.

======================================================

### Slide 9
**Slide Title:** Novel Contributions

**Bullet Points**
- Innovation
- Unique idea
- Advantages
- Research contribution

**Speaker Notes**
Explain why the work is novel.

======================================================

### Slide 10
**Slide Title:** Limitations & Future Work

**Bullet Points**
- Current limitations
- Remaining challenges
- Future improvements
- Research opportunities

**Speaker Notes**
Discuss future scope.

======================================================

### Slide 11
**Slide Title:** Conclusion

**Bullet Points**
- Summary
- Final outcome
- Key takeaway
- Impact

**Speaker Notes**
Conclude the presentation.

======================================================

Rules:

1. Generate EXACTLY 11 slides.
2. Every slide MUST contain:
   - Slide Title
   - Bullet Points
   - Speaker Notes
3. Maximum 4 bullet points.
4. Maximum 15 words per bullet.
5. Do NOT write paragraphs inside Bullet Points.
6. Speaker Notes should be concise (2–3 sentences).
7. Use ONLY information from the uploaded paper.
8. Never invent datasets.
9. Never invent citations.
10. Never invent references.
11. Never invent numerical values.
12. If information is unavailable, write:
    "Not available in the uploaded paper."
13. Output ONLY the slides in the specified format.
"""

    return generate_answer(
        context=context,
        question=question,
    )


# ==========================================================
# Workspace PPT Generator Agent
# ==========================================================

def run_ppt_agent(topic: str, papers) -> str:
    """
    Execute the PPT Generator Agent.
    """

    print("Running PPT Generator Agent...")

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

    return generate_presentation(context)