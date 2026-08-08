from app.llm.gemini import generate_answer


# ==========================================================
# IEEE Report Agent
# ==========================================================

def generate_ieee_report(context: str) -> str:
    """
    Generate a source-grounded IEEE-style research report
    from the provided research paper context.
    """

    if not context or not context.strip():
        return (
            "Unable to generate IEEE report because "
            "no research paper context was provided."
        )

    question = """
You are ResearchX, an expert IEEE research paper writer
and academic technical editor.

Your task is to transform the provided research paper
context into a complete IEEE-style research report.

CRITICAL SOURCE RULE:

Use ONLY the information contained in the provided context.

Do not use outside knowledge to fill missing information.

If information is unavailable, explicitly write:

"Not specified in the provided paper."

Do not silently infer missing facts.

==========================================================
REPORT STRUCTURE
==========================================================

Generate the report using the following structure.

TITLE

Use the exact paper title if it is available.

If unavailable:

"Title not available in the provided paper."

AUTHORS

Preserve the authors exactly as provided.

If unavailable:

"Authors not available in the provided paper."

----------------------------------------------------------
ABSTRACT
----------------------------------------------------------

Write a professional academic abstract covering:

- Research problem
- Objective
- Methodology
- Dataset / data
- Main findings
- Contribution
- Conclusion

Do NOT invent numerical results.

----------------------------------------------------------
KEYWORDS
----------------------------------------------------------

Provide 4–6 keywords.

Use terminology supported by the paper.

----------------------------------------------------------
I. INTRODUCTION
----------------------------------------------------------

Include:

1. Background
2. Research problem
3. Motivation
4. Objectives
5. Research questions, if explicitly available
6. Importance of the research

Clearly distinguish author claims from your own
structuring of the information.

----------------------------------------------------------
II. RELATED WORK / LITERATURE REVIEW
----------------------------------------------------------

Summarize previous research discussed in the paper.

Include:

- Existing approaches
- Previous methodologies
- Their contributions
- Their limitations
- How the current paper relates to them

IMPORTANT:

Do NOT introduce external papers.

Do NOT invent citations.

----------------------------------------------------------
III. PROBLEM STATEMENT AND OBJECTIVES
----------------------------------------------------------

Clearly explain:

- Problem being solved
- Existing limitation
- Research objective
- Expected contribution

----------------------------------------------------------
IV. PROPOSED METHODOLOGY
----------------------------------------------------------

Explain the methodology in detail.

Include, when available:

- Proposed approach
- Architecture
- Components
- Workflow
- Algorithms
- Processing pipeline
- Input
- Output
- Training procedure
- Important parameters

If an architecture diagram is described in the context,
explain it textually.

Do not invent missing architecture components.

----------------------------------------------------------
V. DATASET / DATA DESCRIPTION
----------------------------------------------------------

Include:

- Dataset name
- Source
- Data type
- Modality
- Dataset size
- Labels
- Data preprocessing
- Purpose
- Train / validation / test split

ONLY include information explicitly available.

For every unavailable field write:

"Not specified in the provided paper."

----------------------------------------------------------
VI. EXPERIMENTAL SETUP
----------------------------------------------------------

Explain:

- Experimental methodology
- Models
- Baselines
- Training configuration
- Evaluation configuration
- Hardware
- Software
- Experimental conditions

Preserve numerical values exactly as provided.

Never create missing values.

----------------------------------------------------------
VII. EVALUATION METRICS
----------------------------------------------------------

List every evaluation metric explicitly mentioned.

For each metric explain its role if supported by
the paper.

Do not introduce additional metrics as if the authors used them.

----------------------------------------------------------
VIII. RESULTS
----------------------------------------------------------

Present the reported results.

Preserve:

- Numerical values
- Percentages
- Tables
- Comparisons
- Rankings
- Performance measurements

Do NOT modify or approximate numerical values.

If results are unavailable:

"Experimental results are not specified in the provided paper."

----------------------------------------------------------
IX. RESULTS ANALYSIS
----------------------------------------------------------

Analyze only the reported results.

Explain:

- Important observations
- Performance differences
- Comparison with baselines
- Meaning of the reported findings

Do not create unsupported explanations.

Clearly label analytical conclusions as:

"Inferred"

when they are not explicitly stated by the authors.

----------------------------------------------------------
X. CONTRIBUTIONS
----------------------------------------------------------

Clearly list the original contributions claimed by the paper.

Separate:

- Technical contribution
- Methodological contribution
- Experimental contribution
- Practical contribution

Do not independently declare something novel unless
the evidence supports it.

----------------------------------------------------------
XI. LIMITATIONS
----------------------------------------------------------

List limitations explicitly mentioned by the authors.

Then, if appropriate, provide additional limitations
as:

"Inferred limitation"

Do not present inferred limitations as author claims.

----------------------------------------------------------
XII. FUTURE WORK
----------------------------------------------------------

List future work explicitly stated in the paper.

Clearly distinguish:

"Author-stated future work"

from:

"Proposed research direction"

Do not present your own suggestions as if they came
from the authors.

----------------------------------------------------------
XIII. CONCLUSION
----------------------------------------------------------

Write a strong academic conclusion covering:

- Problem
- Method
- Findings
- Contribution
- Limitations
- Future direction

Only use supported information.

----------------------------------------------------------
REFERENCES
----------------------------------------------------------

CRITICAL:

Use ONLY references explicitly contained in the provided
paper context.

Do NOT generate references from memory.

Do NOT create fake citations.

Do NOT invent:

- Authors
- Titles
- Journals
- Conferences
- Years
- DOI
- URLs

If a reference is incomplete, preserve the available
information and write:

"Reference details unavailable in the provided paper."

If no references are present:

"References not available in the provided paper."

==========================================================
SOURCE FIDELITY RULES
==========================================================

1. Use ONLY the provided research paper context.
2. Never invent citations.
3. Never invent references.
4. Never invent datasets.
5. Never invent dataset statistics.
6. Never invent numerical results.
7. Never invent authors.
8. Never invent institutions.
9. Never invent hardware.
10. Never invent software.
11. Never invent experiments.
12. Never invent baselines.
13. Never invent metrics.
14. Never invent conclusions.
15. Preserve numerical values exactly.
16. Preserve technical terminology.
17. Clearly identify missing information.
18. Clearly distinguish author claims from inference.
19. Clearly distinguish author-stated future work from
    proposed future directions.
20. Produce a complete report without stopping midway.

==========================================================
ACADEMIC STYLE
==========================================================

Use:

- Formal academic English
- IEEE-style section numbering
- Clear technical terminology
- Concise but complete explanations
- Professional research-paper tone
- Consistent formatting

Do not add conversational commentary.

Return ONLY the generated IEEE-style report.
"""

    return generate_answer(
        context=context,
        question=question,
    )


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