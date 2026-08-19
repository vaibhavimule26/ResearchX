import requests


def search_crossref(topic, limit=10):
    """
    Search research papers using Crossref API.
    """

    url = "https://api.crossref.org/works"

    params = {
        "query": topic,
        "rows": limit
    }

    response = requests.get(url, params=params, timeout=20)

    if response.status_code != 200:
        return []

    data = response.json()

    papers = []

    for item in data["message"]["items"]:

        title = item.get("title", ["No Title"])
        authors = item.get("author", [])
        published = item.get("published-print") or item.get("published-online")

        papers.append({
            "title": title[0] if title else "No Title",
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in authors
            ],
            "summary": "",
            "published": str(
                published["date-parts"][0][0]
            ) if published else "Unknown",
            "pdf_url": "",
            "source": "Crossref"
        })

    return papers