import requests


BASE_URL = "https://api.openalex.org/works"


def search_openalex(topic, limit=20):

    params = {
        "search": topic,
        "per-page": limit,
    }

    response = requests.get(BASE_URL, params=params, timeout=30)

    response.raise_for_status()

    data = response.json()

    papers = []

    for paper in data.get("results", []):

        authors = []

        for author in paper.get("authorships", []):
            if author.get("author"):
                authors.append(author["author"].get("display_name", ""))

        pdf_url = ""

        if paper.get("primary_location"):
            pdf_url = paper["primary_location"].get("pdf_url") or ""

        papers.append(
            {
                "title": paper.get("display_name", ""),
                "authors": authors,
                "summary": paper.get("abstract_inverted_index", {}),
                "published": str(paper.get("publication_year", "")),
                "citation_count": paper.get("cited_by_count", 0),
                "venue": (
                    paper.get("primary_location", {})
                    .get("source", {})
                    .get("display_name", "")
                ),
                "doi": paper.get("doi", ""),
                "pdf_url": pdf_url,
                "source": "OpenAlex",
            }
        )

    return papers