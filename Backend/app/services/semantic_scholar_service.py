import requests


BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_semantic_scholar(topic, limit=20):

    params = {
        "query": topic,
        "limit": limit,
        "fields": "title,authors,abstract,year,citationCount,venue,externalIds,openAccessPdf"
    }

    response = requests.get(BASE_URL, params=params, timeout=30)

    response.raise_for_status()

    data = response.json()

    papers = []

    for paper in data.get("data", []):

        doi = ""

        external_ids = paper.get("externalIds")

        if external_ids:
            doi = external_ids.get("DOI", "")

        pdf_url = ""

        open_access = paper.get("openAccessPdf")

        if open_access:
            pdf_url = open_access.get("url", "")

        papers.append(
            {
                "title": paper.get("title", ""),
                "authors": [
                    author.get("name", "")
                    for author in paper.get("authors", [])
                ],
                "summary": paper.get("abstract", ""),
                "published": str(paper.get("year", "")),
                "citation_count": paper.get("citationCount", 0),
                "venue": paper.get("venue", ""),
                "doi": doi,
                "pdf_url": pdf_url,
                "source": "Semantic Scholar",
            }
        )

    return papers