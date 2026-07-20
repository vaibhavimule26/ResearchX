import arxiv


def search_papers(topic, max_results=10):

    client = arxiv.Client()

    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []

    for paper in client.results(search):

        papers.append(
            {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": str(paper.published.date()),
                "pdf_url": paper.pdf_url,
            }
        )

    return papers