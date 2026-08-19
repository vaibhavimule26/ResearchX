from datetime import datetime
from app.services.similarity_service import calculate_similarity


SOURCE_SCORE = {
    "Semantic Scholar": 10,
    "OpenAlex": 9,
    "Crossref": 8,
    "Arxiv": 7,
}

VENUE_SCORE = {
    "Nature": 10,
    "Science": 10,
    "IEEE": 9,
    "ACM": 9,
    "NeurIPS": 10,
    "ICML": 10,
    "ICLR": 9,
    "CVPR": 9,
    "ECCV": 8,
    "ACL": 8,
    "EMNLP": 8,
}


def calculate_paper_score(paper):

    score = 0

    # ---------- Publication Year ----------
    year = paper.get("published", "")

    try:
        year = int(str(year)[:4])

        current_year = datetime.now().year

        if year >= current_year - 1:
            score += 20
        elif year >= current_year - 3:
            score += 15
        elif year >= current_year - 5:
            score += 10
        else:
            score += 5

    except:
        score += 0

    # ---------- Source Quality ----------
    source = paper.get("source", "")

    score += SOURCE_SCORE.get(source, 5)

    # ---------- Citation Score ----------
    citations = paper.get("citation_count", 0)

    if citations >= 1000:
        score += 20
    elif citations >= 500:
        score += 15
    elif citations >= 100:
        score += 10
    elif citations >= 20:
        score += 5

    # ---------- Venue Quality ----------
    venue = paper.get("venue", "").lower()

    venue_score = 0

    for key, value in VENUE_SCORE.items():
        if key.lower() in venue:
            venue_score = value
            break

    score += venue_score

    paper["ranking_reason"] = {
        "semantic_score": round(paper.get("semantic_score", 0), 3),
        "citation_count": paper.get("citation_count", 0),
        "publication_year": paper.get("published", ""),
        "venue": paper.get("venue", ""),
        "source": paper.get("source", ""),
    }

    paper["researchx_score"] = score

    return paper


def rank_papers(query, papers):

    papers = calculate_similarity(query, papers)

    ranked = []

    for paper in papers:

        paper = calculate_paper_score(paper)

        semantic = paper.get("semantic_score", 0)

        paper["researchx_score"] += semantic * 40

        ranked.append(paper)

    ranked.sort(
        key=lambda x: x["researchx_score"],
        reverse=True
    )

    return ranked