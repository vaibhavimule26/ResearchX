# Backend/app/search/paper_search_service.py

import asyncio
import os
import re
from typing import Any, Dict, List

import cohere
import httpx
from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# Common Paper Format
# ==========================================================

def normalize_paper(
    title="",
    authors=None,
    summary="",
    published="N/A",
    pdf_url=None,
    url=None,
    source="Unknown",
    citations=0,
    doi=None,
):
    return {
        "title": title or "",
        "authors": authors or [],
        "summary": summary or "Abstract not available.",
        "abstract": summary or "Abstract not available.",
        "published": str(published) if published else "N/A",
        "pdf_url": pdf_url,
        "url": url,
        "source": source,
        "citations": citations or 0,
        "doi": doi,
    }


# ==========================================================
# 1. arXiv
# ==========================================================

async def fetch_arxiv_papers(query: str, limit: int = 30):
    papers = []

    url = "https://export.arxiv.org/api/query"

    params = {
        "search_query": f'all:"{query}"',
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        entries = re.findall(
            r"<entry>(.*?)</entry>",
            response.text,
            re.DOTALL
        )

        for entry in entries:
            title_match = re.search(
                r"<title>(.*?)</title>",
                entry,
                re.DOTALL
            )

            summary_match = re.search(
                r"<summary>(.*?)</summary>",
                entry,
                re.DOTALL
            )

            published_match = re.search(
                r"<published>(.*?)</published>",
                entry
            )

            id_match = re.search(
                r"<id>(.*?)</id>",
                entry
            )

            author_matches = re.findall(
                r"<name>(.*?)</name>",
                entry
            )

            if not title_match or not id_match:
                continue

            title = re.sub(
                r"\s+",
                " ",
                title_match.group(1)
            ).strip()

            summary = (
                re.sub(
                    r"\s+",
                    " ",
                    summary_match.group(1)
                ).strip()
                if summary_match
                else "Abstract not available."
            )

            published = (
                published_match.group(1)[:10]
                if published_match
                else "N/A"
            )

            paper_url = id_match.group(1).strip()

            pdf_url = paper_url.replace(
                "/abs/",
                "/pdf/"
            ) + ".pdf"

            papers.append(
                normalize_paper(
                    title=title,
                    authors=author_matches[:10],
                    summary=summary,
                    published=published,
                    pdf_url=pdf_url,
                    url=paper_url,
                    source="arXiv",
                    citations=0,
                    doi=None,
                )
            )

    except Exception as e:
        print(f"[arXiv Error] {e}")

    return papers


# ==========================================================
# 2. Semantic Scholar
# ==========================================================

async def fetch_semantic_scholar_papers(
    query: str,
    limit: int = 30
):
    papers = []

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": limit,
        "fields": (
            "title,abstract,year,url,citationCount,"
            "venue,authors,openAccessPdf,externalIds"
        ),
    }

    headers = {
        "User-Agent": "ResearchX/1.0"
    }

    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    if api_key:
        headers["x-api-key"] = api_key
    else:
        print("[Semantic Scholar] No API key found - using public access")

    max_retries = 5

    try:
        async with httpx.AsyncClient(
            timeout=30,
            headers=headers
        ) as client:

            data = None
            for attempt in range(max_retries):

                response = await client.get(url, params=params)

                # Success
                if response.status_code == 200:
                    data = response.json()
                    break

                # Rate limit - wait and retry
                if response.status_code == 429:
                    wait_time = min(2 ** attempt, 30)

                    print(
                        f"[Semantic Scholar] Rate limited. "
                        f"Waiting {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )

                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()

            else:
                print(
                    "[Semantic Scholar] Max retries reached. "
                    "Skipping this source."
                )
                return papers

        if not data:
            return papers

        for paper in data.get("data", []):

            title = paper.get("title")

            if not title:
                continue

            authors = [
                author.get("name")
                for author in paper.get("authors", [])
                if author.get("name")
            ]

            abstract = (
                paper.get("abstract")
                or "Abstract not available."
            )

            open_access = paper.get("openAccessPdf") or {}

            doi = (
                paper.get("externalIds") or {}
            ).get("DOI")

            papers.append(
                normalize_paper(
                    title=title,
                    authors=authors[:10],
                    summary=abstract,
                    published=paper.get("year") or "N/A",
                    pdf_url=open_access.get("url"),
                    url=paper.get("url"),
                    source="Semantic Scholar",
                    citations=paper.get("citationCount", 0),
                    doi=doi,
                )
            )

        print(f"[Semantic Scholar] Found {len(papers)} papers")

    except Exception as e:
        print(f"[Semantic Scholar Error] {e}")

    return papers


# ==========================================================
# 3. OpenAlex
# ==========================================================

async def fetch_openalex_papers(
    query: str,
    limit: int = 30
):
    papers = []

    url = "https://api.openalex.org/works"

    params = {
        "search": query,
        "per-page": limit,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

        for work in data.get("results", []):

            title = work.get("display_name")

            if not title:
                continue

            authors = []

            for authorship in work.get(
                "authorships",
                []
            ):
                author = authorship.get("author", {})
                name = author.get("display_name")

                if name:
                    authors.append(name)

            # OpenAlex stores abstract as inverted index
            abstract_index = work.get(
                "abstract_inverted_index"
            )

            abstract = "Abstract not available."

            if abstract_index:
                positions = []

                for word, indexes in abstract_index.items():
                    for index in indexes:
                        positions.append(
                            (index, word)
                        )

                positions.sort()

                abstract = " ".join(
                    word for _, word in positions
                )

            doi = work.get("doi")

            if doi:
                doi = doi.replace(
                    "https://doi.org/",
                    ""
                )

            primary_location = (
                work.get("primary_location") or {}
            )

            best_oa_location = (
                work.get("best_oa_location") or {}
            )

            landing_page = (
                primary_location.get("landing_page_url")
                or work.get("doi")
                or work.get("id")
            )

            pdf_url = (
                primary_location.get("pdf_url")
                or best_oa_location.get("pdf_url")
            )

            papers.append(
                normalize_paper(
                    title=title,
                    authors=authors[:10],
                    summary=abstract,
                    published=work.get(
                        "publication_date"
                    ) or work.get(
                        "publication_year"
                    ) or "N/A",
                    pdf_url=pdf_url,
                    url=landing_page,
                    source="OpenAlex",
                    citations=work.get(
                        "cited_by_count",
                        0
                    ),
                    doi=doi,
                )
            )

    except Exception as e:
        print(f"[OpenAlex Error] {e}")

    return papers


# ==========================================================
# 4. Crossref
# ==========================================================

async def fetch_crossref_papers(
    query: str,
    limit: int = 30
):
    papers = []

    url = "https://api.crossref.org/works"

    params = {
        "query": query,
        "rows": limit,
        "select": (
            "DOI,title,author,abstract,published,"
            "published-print,published-online,"
            "URL,container-title,is-referenced-by-count"
        ),
    }

    headers = {
        "User-Agent": "ResearchX/1.0"
    }

    try:
        async with httpx.AsyncClient(
            timeout=30,
            headers=headers
        ) as client:

            response = await client.get(
                url,
                params=params
            )

            response.raise_for_status()

            data = response.json()

        items = (
            data.get("message", {})
            .get("items", [])
        )

        for item in items:

            title_list = item.get("title", [])

            if not title_list:
                continue

            title = title_list[0]

            authors = []

            for author in item.get("author", []):

                name = " ".join(
                    filter(
                        None,
                        [
                            author.get("given"),
                            author.get("family"),
                        ]
                    )
                )

                if name:
                    authors.append(name)

            abstract = (
                item.get("abstract")
                or "Abstract not available."
            )

            # Remove HTML tags from Crossref abstracts
            abstract = re.sub(
                r"<[^>]+>",
                "",
                abstract
            )

            date_parts = None

            for date_field in [
                "published-print",
                "published-online",
                "published",
            ]:
                if item.get(date_field):
                    date_parts = (
                        item[date_field]
                        .get("date-parts", [])
                    )
                    if date_parts:
                        break

            published = "N/A"

            if date_parts and date_parts[0]:

                parts = date_parts[0]

                if len(parts) >= 3:
                    published = (
                        f"{parts[0]}-"
                        f"{str(parts[1]).zfill(2)}-"
                        f"{str(parts[2]).zfill(2)}"
                    )

                elif len(parts) == 2:
                    published = (
                        f"{parts[0]}-"
                        f"{str(parts[1]).zfill(2)}"
                    )

                else:
                    published = str(parts[0])

            doi = item.get("DOI")

            papers.append(
                normalize_paper(
                    title=title,
                    authors=authors[:10],
                    summary=abstract,
                    published=published,
                    pdf_url=None,
                    url=item.get("URL"),
                    source="Crossref",
                    citations=item.get(
                        "is-referenced-by-count",
                        0
                    ),
                    doi=doi,
                )
            )

    except Exception as e:
        print(f"[Crossref Error] {e}")

    return papers


# ==========================================================
# 5. IEEE Xplore
# ==========================================================

async def fetch_ieee_papers(
    query: str,
    limit: int = 30
):
    papers = []

    api_key = os.getenv("IEEE_API_KEY")

    if not api_key:
        print("[IEEE] IEEE_API_KEY not found in .env")
        return papers

    url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    params = {
        "apikey": api_key,
        "querytext": query,
        "max_records": limit,
        "start_record": 1,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                url,
                params=params
            )

            response.raise_for_status()
            data = response.json()

        for article in data.get("articles", []):

            title = article.get("title")

            if not title:
                continue

            authors = []

            author_data = article.get("authors") or {}

            for author in author_data.get("authors", []):
                name = author.get("full_name")

                if name:
                    authors.append(name)

            abstract = (
                article.get("abstract")
                or "Abstract not available."
            )

            pdf_url = article.get("pdf_url")

            article_url = (
                article.get("html_url")
                or article.get("abstract_url")
                or article.get("article_url")
            )

            doi = article.get("doi")

            published = (
                article.get("publication_date")
                or article.get("publication_year")
                or "N/A"
            )

            papers.append(
                normalize_paper(
                    title=title,
                    authors=authors[:10],
                    summary=abstract,
                    published=published,
                    pdf_url=pdf_url,
                    url=article_url,
                    source="IEEE Xplore",
                    citations=article.get(
                        "citing_paper_count",
                        0
                    ),
                    doi=doi,
                )
            )

        print(f"[IEEE] Found {len(papers)} papers")

    except Exception as e:
        print(f"[IEEE Error] {e}")

    return papers


# ==========================================================
# Duplicate Removal
# ==========================================================

def remove_duplicate_papers(papers):
    unique_papers = []
    seen_dois = set()
    seen_titles = set()

    for paper in papers:

        # Normalize DOI
        doi = (paper.get("doi") or "").strip().lower()

        # Normalize title
        title = (paper.get("title") or "").strip().lower()
        normalized_title = " ".join(title.split())

        # Skip duplicate DOI
        if doi and doi in seen_dois:
            continue

        # Skip duplicate title
        if normalized_title and normalized_title in seen_titles:
            continue

        # Save unique identifiers
        if doi:
            seen_dois.add(doi)

        if normalized_title:
            seen_titles.add(normalized_title)

        unique_papers.append(paper)

    return unique_papers


# ==========================================================
# Cohere Relevance Reranking & Query-Focus Filtering
# ==========================================================

def is_query_focused(query: str, paper: dict) -> bool:
    """
    Reject papers where the query is only an application context
    and keep papers directly focused on the user's research topic.
    """

    query_words = [
        word.lower()
        for word in query.split()
        if len(word) > 2
    ]

    title = paper.get("title", "").lower()
    abstract = paper.get("abstract", "").lower()

    # At least 70% of important query words must appear
    # in title or abstract
    if not query_words:
        return True

    matched_words = sum(
        1 for word in query_words
        if word in title or word in abstract
    )

    focus_score = matched_words / len(query_words)

    paper["focus_score"] = round(focus_score * 100, 2)

    return focus_score >= 0.70


def is_application_specific(query: str, paper: dict) -> bool:
    """
    Detect whether a paper applies the user's topic to a specific domain
    instead of studying the topic itself.
    """

    title = paper.get("title", "").lower()

    application_patterns = [
        "for epidemiological",
        "for autonomous",
        "for financial",
        "for vehicle",
        "for human-robot",
        "for robot",
        "for healthcare",
        "for medical",
        "for network security",
        "for customer",
        "for manufacturing",
        "for education",
        "for agriculture",
        "for modeling",
        "for image",
        "for vision",
        "for routing",
        "for specific"
    ]

    # Only apply this filter for short/general research topics
    if len(query.split()) <= 4:
        return any(pattern in title for pattern in application_patterns)

    return False


async def ai_relevance_check(query: str, paper: dict) -> bool:
    """
    Final AI semantic relevance validation.
    Keeps papers whose main contribution is genuinely related
    to the user's research query.
    """

    from groq import AsyncGroq

    client = AsyncGroq(
        api_key=os.getenv("GROQ_API_KEY")
    )

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    prompt = f"""
You are an expert research paper relevance evaluator.

USER RESEARCH QUERY:
{query}

PAPER TITLE:
{title}

PAPER ABSTRACT:
{abstract[:3000]}

TASK:
Determine whether this paper is genuinely relevant to the user's
research query based on its main research contribution.

RELEVANT means:
- The paper directly studies the query topic, OR
- The paper studies an important architecture, framework, method,
  design, evaluation, comparison, survey, challenge, or implementation
  closely related to the query topic.

IRRELEVANT means:
- The query topic is only a minor tool or technique used in an
  unrelated domain.
- The paper's main contribution is about a completely different
  application domain.
- The connection is based only on keyword overlap.

IMPORTANT:
Do NOT require an exact title match.

For example, for the query "Agentic Framework":
RELEVANT:
- Agentic AI architectures
- Agentic system frameworks
- Agent orchestration frameworks
- Multi-agent architectures
- Framework design and evaluation for agentic AI
- Surveys or comparisons of agentic frameworks

IRRELEVANT:
- An agentic framework whose main contribution is specifically
  vehicle routing, epidemiology, industrial inspection, financial
  services, robotics, or another unrelated application domain.

Consider the TITLE and ABSTRACT together.

Return ONLY:
RELEVANT
or
IRRELEVANT
"""

    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=200
        )

        raw_content = response.choices[0].message.content

        print(f"[ResearchX] Raw AI response: {raw_content!r}")

        decision = (raw_content or "").strip().upper()

        # Fallback: check reasoning field if content is empty
        if not decision:
            reasoning = getattr(
                response.choices[0].message,
                "reasoning",
                None
            )

            print(f"[ResearchX] AI reasoning: {reasoning!r}")

            decision = (reasoning or "").strip().upper()

        # Extract the final classification safely
        if "RELEVANT" in decision and "IRRELEVANT" not in decision:
            decision = "RELEVANT"
        elif "IRRELEVANT" in decision:
            decision = "IRRELEVANT"
        else:
            decision = "IRRELEVANT"

        print(
            f"[ResearchX] Final AI relevance decision: "
            f"{decision} | {title}"
        )

        return decision == "RELEVANT"

    except Exception as e:
        print(f"[ResearchX] AI relevance check failed: {e}")
        return True


# ==========================================================
# Paper Accessibility Validation & Link Normalization
# ==========================================================

def has_accessible_link(paper: Dict[str, Any]) -> bool:
    """
    Keep only papers with a directly accessible PDF.
    Papers without a PDF are rejected.
    """

    pdf_url = paper.get("pdf_url") or ""

    if not pdf_url:
        return False

    pdf_url = str(pdf_url).strip()

    return pdf_url.startswith("http://") or pdf_url.startswith("https://")


def normalize_paper_links(paper: dict) -> dict:
    """
    Normalize links from all research sources into common fields.
    """

    paper = paper.copy()

    # -------------------------------
    # PDF LINK
    # -------------------------------
    pdf_url = (
        paper.get("pdf_url")
        or paper.get("open_access_pdf")
    )

    # Handle Semantic Scholar openAccessPdf dictionary
    if not pdf_url:
        open_access = paper.get("openAccessPdf")

        if isinstance(open_access, dict):
            pdf_url = open_access.get("url")

        elif isinstance(open_access, str):
            pdf_url = open_access

    paper["pdf_url"] = pdf_url or None

    # -------------------------------
    # PROVIDER / PAPER LINK
    # -------------------------------
    paper_url = (
        paper.get("provider_url")
        or paper.get("source_url")
        or paper.get("url")
        or paper.get("doi_url")
        or paper.get("URL")
    )

    paper["url"] = paper_url or None

    return paper


async def rerank_papers(query: str, papers: list, top_n: int = 30):

    print("[ResearchX] Reranking papers with Cohere...")

    cohere_api_key = os.getenv("COHERE_API_KEY")

    if not cohere_api_key:
        print("[ResearchX] COHERE_API_KEY not found")
        return papers[:top_n]

    try:
        co = cohere.Client(cohere_api_key)

        documents = []

        for paper in papers:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")

            # Cohere will compare the complete query
            # against paper title + abstract
            documents.append(
                f"Title: {title}\nAbstract: {abstract}"
            )

        candidate_count = min(top_n, len(documents))

        response = co.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=documents,
            top_n=candidate_count,
        )

        ranked_papers = []

        for result in response.results:
            paper = papers[result.index].copy()
            paper["relevance_score"] = result.relevance_score
            ranked_papers.append(paper)

        return ranked_papers

    except Exception as e:
        print(f"[Cohere Reranking Error] {e}")
        return papers[:top_n]


# ==========================================================
# 6. Multi-Source Search
# ==========================================================

async def search_all_sources(
    query: str,
    limit_per_source: int = 30
) -> List[Dict[str, Any]]:

    print(
        f"\n[ResearchX] Searching all sources for: {query}"
    )

    results = await asyncio.gather(
        fetch_ieee_papers(
            query,
            limit_per_source
        ),
        fetch_arxiv_papers(
            query,
            limit_per_source
        ),
        fetch_semantic_scholar_papers(
            query,
            limit_per_source
        ),
        fetch_openalex_papers(
            query,
            limit_per_source
        ),
        fetch_crossref_papers(
            query,
            limit_per_source
        ),
        return_exceptions=True,
    )

    all_papers = []

    source_names = [
        "IEEE Xplore",
        "arXiv",
        "Semantic Scholar",
        "OpenAlex",
        "Crossref",
    ]

    for source_name, result in zip(
        source_names,
        results
    ):
        if isinstance(result, Exception):
            print(
                f"[{source_name} Error] {result}"
            )
        else:
            print(
                f"[{source_name}] Found {len(result)} papers"
            )
            all_papers.extend(result)

    print(
        f"[ResearchX] Total candidates: {len(all_papers)}"
    )

    unique_papers = remove_duplicate_papers(all_papers)

    print(
        f"[ResearchX] After duplicate removal: "
        f"{len(unique_papers)} unique papers"
    )

    # Normalize all source-specific links
    normalized_papers = [
        normalize_paper_links(paper)
        for paper in unique_papers
    ]

    # Keep only papers researchers can actually open
    accessible_papers = [
        paper for paper in normalized_papers
        if has_accessible_link(paper)
    ]

    print(
        f"[ResearchX] Accessible papers: "
        f"{len(accessible_papers)}"
    )

    # Rerank accessible candidate papers with Cohere
    reranked_papers = await rerank_papers(
        query,
        accessible_papers,
        top_n=30
    )

    # Strict Relevance Filtering
    strictly_relevant_papers = []

    for paper in reranked_papers:
        if len(strictly_relevant_papers) >= 10:
            break

        # Cohere relevance threshold
        if paper.get("relevance_score", 0.0) < 0.60:
            continue

        # Query-focus validation
        if not is_query_focused(query, paper):
            print(
                f"[ResearchX] Rejected - low query focus: "
                f"{paper.get('title')}"
            )
            continue

        # Reject application-specific papers for a general research query
        if is_application_specific(query, paper):
            print(
                f"[ResearchX] Rejected - application-specific: "
                f"{paper.get('title')}"
            )
            continue

        # Final AI semantic relevance validation
        is_relevant = await ai_relevance_check(query, paper)

        if not is_relevant:
            print(
                f"[ResearchX] Rejected by AI relevance judge: "
                f"{paper.get('title')}"
            )
            continue

        strictly_relevant_papers.append(paper)

    print(f"[ResearchX] Strictly relevant papers: {len(strictly_relevant_papers)}")

    # ==========================================================
    # FINAL PAPER SELECTION
    # Always try to return up to 10 accessible papers
    # ==========================================================

    final_papers = []

    # Priority 1: Strictly AI-relevant papers
    final_papers.extend(strictly_relevant_papers[:10])

    # Priority 2: If fewer than 10 strict matches exist,
    # fill remaining slots using the highest-ranked accessible papers
    if len(final_papers) < 10:

        print(
            f"[ResearchX] Only {len(final_papers)} strictly relevant papers found. "
            "Filling remaining slots from top accessible reranked papers..."
        )

        existing_titles = {
            paper.get("title", "").strip().lower()
            if isinstance(paper, dict)
            else getattr(paper, "title", "").strip().lower()
            for paper in final_papers
        }

        for paper in reranked_papers:

            title = (
                paper.get("title", "").strip().lower()
                if isinstance(paper, dict)
                else getattr(paper, "title", "").strip().lower()
            )

            # Skip duplicates
            if title in existing_titles:
                continue

            final_papers.append(paper)
            existing_titles.add(title)

            if len(final_papers) >= 10:
                break

    print(f"[ResearchX] Final papers selected: {len(final_papers)}")

    print("\n========== FINAL PAPER LINKS ==========")

    for i, paper in enumerate(final_papers, 1):
        print(f"\nPaper {i}: {paper.get('title')}")
        print("pdf_url:", paper.get("pdf_url"))
        print("url:", paper.get("url"))
        print("provider_url:", paper.get("provider_url"))
        print("source_url:", paper.get("source_url"))
        print("doi_url:", paper.get("doi_url"))

    print("\n=======================================\n")

    print(f"[ResearchX] Returning {len(final_papers)} papers")

    return final_papers[:10]