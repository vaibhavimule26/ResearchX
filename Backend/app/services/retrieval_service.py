from app.services.arxiv_service import search_papers as search_arxiv
from app.services.semantic_scholar_service import search_semantic_scholar
from app.services.openalex_service import search_openalex


def search_papers(topic):

    papers = []

    try:
        papers.extend(search_arxiv(topic, max_results=10))
    except Exception as e:
        print("Arxiv Error:", e)

    try:
        papers.extend(search_semantic_scholar(topic, limit=10))
    except Exception as e:
        print("Semantic Scholar Error:", e)

    try:
        papers.extend(search_openalex(topic, limit=10))
    except Exception as e:
        print("OpenAlex Error:", e)

    return papers