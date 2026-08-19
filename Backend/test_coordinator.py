from app.agents.coordinator import run_agent

context = """
Artificial Intelligence in Healthcare

This paper proposes a deep learning model for disease prediction
using chest X-ray images.
"""

queries = [

    "Summarize this paper",

    "Find research gaps",

    "Recommend datasets",

    "Recommend experiments",

    "Analyze novelty",

    "Generate literature survey",

    "Complete analysis"

]

for q in queries:

    print("=" * 70)

    print("QUERY :", q)

    print("=" * 70)

    result = run_agent(q, context)

    print(result)

    print("\n")