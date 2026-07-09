def generate_final_report(
    summary,
    gaps,
    datasets,
    experiments,
    literature,
    novelty,
):
    """
    Combine outputs from all agents into one report.
    """

    report = f"""
# Research Paper Analysis Report

## 1. Summary

{summary}

--------------------------------------------------

## 2. Research Gaps

{gaps}

--------------------------------------------------

## 3. Recommended Datasets

{datasets}

--------------------------------------------------

## 4. Recommended Experiments

{experiments}

--------------------------------------------------

## 5. Literature Survey

{literature}

--------------------------------------------------

## 6. Novelty Analysis

{novelty}

--------------------------------------------------

End of Report.
"""

    return report