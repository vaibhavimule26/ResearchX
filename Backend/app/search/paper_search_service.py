# Backend/app/search/paper_search_service.py

import asyncio
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

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
    venue=None,
    relevance_score=0.0,
):
    import urllib.parse

    published_str = str(published) if published else "N/A"

    year = None
    year_match = re.search(r"\b(19|20)\d{2}\b", published_str)

    if year_match:
        year = int(year_match.group(0))

    # Clean and resolve DOI
    clean_doi = None
    if doi:
        clean_doi = str(doi).replace("https://doi.org/", "").replace("http://doi.org/", "").strip()

    resolved_url = url
    resolved_pdf = pdf_url

    # Auto-resolve arXiv PDF URLs
    if resolved_url and "arxiv.org/abs/" in resolved_url:
        resolved_pdf = resolved_url.replace("/abs/", "/pdf/")
        if not resolved_pdf.endswith(".pdf"):
            resolved_pdf += ".pdf"
    elif resolved_url and "arxiv.org/pdf/" in resolved_url:
        resolved_pdf = resolved_url
        resolved_url = resolved_url.replace("/pdf/", "/abs/").replace(".pdf", "")

    # Auto-resolve DOI links
    if clean_doi:
        if not resolved_url:
            resolved_url = f"https://doi.org/{clean_doi}"
        if not resolved_pdf:
            if "10.48550/arxiv." in clean_doi.lower():
                arx_match = re.search(r"arxiv\.(\d+\.\d+)", clean_doi, re.IGNORECASE)
                if arx_match:
                    resolved_pdf = f"https://arxiv.org/pdf/{arx_match.group(1)}.pdf"
            else:
                resolved_pdf = resolved_url or f"https://doi.org/{clean_doi}"

    # Guaranteed fallbacks so pdf_url is NEVER empty
    if not resolved_pdf and resolved_url:
        resolved_pdf = resolved_url
    elif not resolved_url and resolved_pdf:
        resolved_url = resolved_pdf
    elif not resolved_pdf and not resolved_url and title:
        encoded_title = urllib.parse.quote(title)
        resolved_url = f"https://scholar.google.com/scholar?q={encoded_title}"
        resolved_pdf = resolved_url

    return {
        "title": title or "",
        "authors": authors or [],
        "summary": summary or "Abstract not available.",
        "abstract": summary or "Abstract not available.",
        "published": published_str,
        "published_date": published_str,
        "year": year,
        "pdf_url": resolved_pdf,
        "url": resolved_url,
        "source": source,
        "venue": venue or "Unknown",
        "citations": citations or 0,
        "citation_count": citations or 0,
        "doi": clean_doi or doi,
        "relevance_score": float(relevance_score or 0.0),
    }


# ==========================================================
# 1. arXiv
# ==========================================================

async def fetch_arxiv_papers(query: str, limit: int = 30):
    papers = []

    url = "https://export.arxiv.org/api/query"

    # Clean query for arXiv: remove punctuation, extract keywords, avoid rigid full-sentence quotes
    clean_query = re.sub(r"[^\w\s\-\+]", " ", query).strip()
    terms = clean_query.split()
    if len(terms) > 6:
        # For long sentences, use the core terms with AND
        arxiv_search_term = " AND ".join(f"all:{t}" for t in terms[:6])
    elif len(terms) > 1:
        arxiv_search_term = f'all:({" ".join(terms)})'
    else:
        arxiv_search_term = f"all:{clean_query}" if clean_query else "all:research"

    params = {
        "search_query": arxiv_search_term,
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
                    venue="arXiv",
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
                    venue=paper.get("venue"),
                )
            )

        print(f"[Semantic Scholar] Found {len(papers)} papers")

    except Exception as e:
        print(f"[Semantic Scholar Error] {e}")

    return papers


# ==========================================================
# 3. OpenAlex
# ==========================================================

def reconstruct_openalex_abstract(inverted_index: Optional[dict]) -> str:
    """Reconstruct human-readable abstract from OpenAlex abstract_inverted_index."""
    if not inverted_index or not isinstance(inverted_index, dict):
        return ""
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            if isinstance(positions, list):
                for pos in positions:
                    word_positions.append((pos, str(word)))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions).strip()
    except Exception:
        return ""


async def fetch_openalex_papers(
    query: str,
    limit: int = 30,
    ieee_only: bool = False,
):
    papers = []
    url = "https://api.openalex.org/works"

    search_query = f"IEEE {query}" if ieee_only else query
    params = {
        "search": search_query,
        "per_page": limit,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        for work in data.get("results", []):
            title = work.get("title")
            if not title:
                continue

            authors = [
                auth.get("author", {}).get("display_name")
                for auth in work.get("authorships", [])
                if auth.get("author", {}).get("display_name")
            ]

            reconstructed_abstract = reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
            abstract = reconstructed_abstract or work.get("abstract") or "Abstract not available."
            doi = work.get("doi")
            primary_location = work.get("primary_location") or {}
            best_oa_location = work.get("best_oa_location") or {}

            landing_page = (
                primary_location.get("landing_page_url")
                or work.get("doi")
                or work.get("id")
            )

            pdf_url = (
                primary_location.get("pdf_url")
                or best_oa_location.get("pdf_url")
            )

            source_venue = (
                primary_location.get("source", {}).get("display_name")
                if primary_location.get("source")
                else None
            )

            is_ieee = bool(
                (source_venue and "ieee" in source_venue.lower())
                or (doi and "10.1109" in str(doi).lower())
                or (landing_page and "ieee.org" in str(landing_page).lower())
            )

            if ieee_only and not is_ieee:
                continue

            papers.append(
                normalize_paper(
                    title=title,
                    authors=authors[:10],
                    summary=abstract,
                    published=work.get("publication_date") or work.get("publication_year") or "N/A",
                    pdf_url=pdf_url,
                    url=landing_page,
                    source="IEEE (OpenAlex)" if is_ieee else "OpenAlex",
                    citations=work.get("cited_by_count", 0),
                    doi=doi,
                    venue=source_venue or ("IEEE Publication" if is_ieee else "Academic Source"),
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
    limit: int = 30,
    ieee_only: bool = False,
):
    papers = []
    url = "https://api.crossref.org/works"

    search_query = f"IEEE {query}" if ieee_only else query
    params = {
        "query": search_query,
        "rows": limit,
        "select": (
            "DOI,title,author,abstract,published,"
            "published-print,published-online,"
            "URL,container-title,is-referenced-by-count"
        ),
    }

    if ieee_only:
        params["filter"] = "prefix:10.1109"

    headers = {"User-Agent": "ResearchX/1.0"}

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
            container_titles = item.get("container-title", [])
            venue = container_titles[0] if container_titles else None

            if ieee_only and "ieee" not in str(venue).lower():
                continue

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
                    venue=venue,
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

            venue = article.get("publication_title") or article.get("conference_name")

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
                    venue=venue,
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
# AI Semantic Relevance Validation (Preserved for Future Use)
# ==========================================================

async def ai_relevance_check(query: str, paper: dict) -> bool:
    """
    AI-based semantic relevance validation.

    Checks the actual research intent instead of relying only
    on keyword overlap.
    """

    from groq import AsyncGroq

    client = AsyncGroq(
        api_key=os.getenv("GROQ_API_KEY")
    )

    title = str(paper.get("title") or "")
    abstract = str(
        paper.get("abstract")
        or paper.get("summary")
        or ""
    )

    prompt = f"""
You are an expert academic research relevance evaluator.

USER RESEARCH QUERY:{query}

PAPER TITLE:{title}

PAPER ABSTRACT:{abstract[:5000]}

Determine whether the paper is genuinely relevant to the
user's research query.

The query can belong to ANY academic or scientific domain.

Evaluate semantic meaning, not simple keyword overlap.

A paper is RELEVANT when:

- Its main research contribution directly addresses the query, OR
- It presents a method, architecture, framework, model, algorithm,
  experiment, dataset, evaluation, survey, review, comparison,
  theory, or implementation that is substantially related to
  the research topic.

A paper can still be relevant when:
- its title uses different terminology,
- it uses synonyms,
- it uses an established technical term instead of the wording
  used by the user,
- the query is written as a natural-language sentence,
- the query contains spelling mistakes that were corrected.

A paper is IRRELEVANT when:
- the connection is only a superficial keyword match,
- the query concept is only a minor unrelated component,
- the paper's primary research contribution belongs to a
  substantially different topic.

IMPORTANT:

- Do NOT assume any particular research domain.
- Do NOT require exact title matching.
- Do NOT reject a paper merely because terminology differs.
- Judge the relationship between the QUERY and the PAPER'S
  MAIN RESEARCH CONTRIBUTION.
- Do not invent relevance that is not supported by the title
  or abstract.

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
            max_tokens=20,
        )

        raw_content = (
            response.choices[0].message.content or ""
        ).strip().upper()

        print(
            f"[ResearchX] AI relevance: "
            f"{title} -> {raw_content!r}"
        )

        if "RELEVANT" in raw_content and "IRRELEVANT" not in raw_content:
            return True

        return False

    except Exception as e:
        print(
            f"[AI Relevance Error] {e}"
        )

        # Do not destroy search results if AI validation fails.
        return True


# ==========================================================
# Paper Accessibility Validation & Link Normalization
# ==========================================================

def has_accessible_link(paper: Dict[str, Any]) -> bool:
    """
    Keep papers that have a usable web link.
    Prefer PDF links, but allow valid article/source links too.
    """

    possible_links = [
        paper.get("pdf_url"),
        paper.get("open_access_pdf"),
        paper.get("url"),
        paper.get("source_url"),
        paper.get("provider_url"),
        paper.get("doi_url"),
    ]

    for link in possible_links:
        if isinstance(link, dict):
            link = link.get("url")

        if link:
            link = str(link).strip()

            if link.startswith("http://") or link.startswith("https://"):
                return True

    return False


def normalize_workspace_query(query: str) -> str:
    """
    Clean natural-language search instructions while preserving
    the actual research topic.

    Domain-agnostic: works for any academic field.
    """

    if not query:
        return ""

    query = str(query).strip()

    # Remove only conversational search prefixes.
    query = re.sub(
        r"^\s*"
        r"(give\s+me|show\s+me|find\s+me|find|"
        r"search\s+for|search|get\s+me)"
        r"\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Remove generic paper-request wording.
    query = re.sub(
        r"\b(?:some\s+)?(?:research\s+)?papers?\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Remove generic filler phrases.
    query = re.sub(
        r"\b(?:about|regarding|related\s+to)\b",
        " ",
        query,
        flags=re.IGNORECASE,
    )

    # Keep technical characters such as:
    # +, #, -, /, ., etc. where possible.
    query = re.sub(
        r"[^\w\s\-\+\#\/\.]",
        " ",
        query,
        flags=re.UNICODE,
    )

    query = re.sub(r"\s+", " ", query).strip()

    return query


async def correct_query_spelling(query: str) -> str:
    """
    Generic AI-based correction for arbitrary research queries.
    Domain-agnostic, fixes spelling, typos, and syntax while preserving research intent.
    """
    if not query or not query.strip():
        return ""

    raw_query = query.strip()

    prompt = f"""You are an academic research query correction engine.
Your task is ONLY to correct spelling errors, typing mistakes, and obvious spacing mistakes in academic queries.

Rules:
1. Support any academic/scientific domain.
2. Fix misspelled words and technical terms (e.g., 'deeepfake detction' -> 'deepfake detection', 'transfomer netwrok' -> 'transformer network', 'quantm computng' -> 'quantum computing').
3. Preserve the exact research intent.
4. If the query is already correct, return it unchanged.
5. Return ONLY the corrected search query without explanations, quotation marks, or markdown.

Input query: {raw_query}

Corrected query:"""

    # 1. Primary: Groq (llama-3.3-70b-versatile or llama-3.1-8b-instant)
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_api_key)
            for model_candidate in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"]:
                try:
                    response = await client.chat.completions.create(
                        model=model_candidate,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_tokens=100,
                    )
                    corrected = (response.choices[0].message.content or "").strip()
                    corrected = re.sub(r"^```(?:text)?\s*", "", corrected, flags=re.IGNORECASE)
                    corrected = re.sub(r"\s*```$", "", corrected)
                    corrected = corrected.strip().strip('"').strip("'")
                    if corrected and len(corrected) > 2 and "\n" not in corrected:
                        print(f"[Query Correction Groq] '{raw_query}' -> '{corrected}'")
                        return corrected
                except Exception as model_err:
                    print(f"[Query Correction Groq Model {model_candidate}]: {model_err}")
                    continue
        except Exception as e:
            print(f"[Query Correction Groq Error] {e}")

    # 2. Secondary: Mistral
    mistral_api_key = os.getenv("MISTRAL_API_KEY")
    if mistral_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as http_client:
                res = await http_client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {mistral_api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "mistral-small-latest",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0,
                        "max_tokens": 100,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    corrected = data["choices"][0]["message"]["content"].strip().strip('"').strip("'")
                    if corrected and "\n" not in corrected:
                        print(f"[Query Correction Mistral] '{raw_query}' -> '{corrected}'")
                        return corrected
        except Exception as e:
            print(f"[Query Correction Mistral Error] {e}")

    return raw_query


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

    if not papers:
        print("[ResearchX] No accessible papers to rerank")
        return []

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
            paper["relevance_score"] = float(result.relevance_score)
            ranked_papers.append(paper)

        return ranked_papers

    except Exception as e:
        print(f"[Cohere Reranking Error] {e}")
        return papers[:top_n]


# ==========================================================
# 6. Multi-Source Search
# ==========================================================

def extract_search_keywords(sentence: str) -> str:
    """
    Extract high-signal academic keywords from natural language sentences
    while preserving technical phrases and terms.
    """
    if not sentence:
        return ""
    
    # Remove conversational prefixes
    cleaned = re.sub(
        r"^(?:please\s+)?(?:can\s+you\s+)?(?:give\s+me|show\s+me|find\s+me|find|search\s+for|search|get\s+me|i\s+want|i\s+need|i\s+am\s+looking\s+for)\s+",
        "",
        sentence.strip(),
        flags=re.IGNORECASE
    )
    # Remove generic academic request phrases
    cleaned = re.sub(
        r"\b(?:some\s+)?(?:recent\s+)?(?:research\s+)?(?:papers?|articles?|studies|literature|publications?)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE
    )
    # Remove generic filler words
    cleaned = re.sub(
        r"\b(?:about|regarding|related\s+to|focusing\s+on|based\s+on|with\s+regard\s+to)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE
    )
    # Clean up whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if len(cleaned) >= 3 else sentence.strip()


async def search_all_sources(
    query: str,
    limit_per_source: int = 30,
    source: str = "all",
) -> List[Dict[str, Any]]:

    search_terms = extract_search_keywords(query)
    print(f"\n[ResearchX] Searching sources for '{query}' (Search terms: '{search_terms}', Filter source: '{source}')")

    is_ieee_filter = bool(source and "ieee" in source.lower())

    tasks = [
        fetch_ieee_papers(search_terms, limit_per_source),
        fetch_arxiv_papers(search_terms, limit_per_source),
        fetch_semantic_scholar_papers(search_terms, limit_per_source),
        fetch_openalex_papers(search_terms, limit_per_source),
        fetch_openalex_papers(search_terms, 30, ieee_only=True),
        fetch_crossref_papers(search_terms, limit_per_source),
        fetch_crossref_papers(search_terms, 30, ieee_only=True),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_papers = []
    source_names = [
        "IEEE Xplore",
        "arXiv",
        "Semantic Scholar",
        "OpenAlex",
        "OpenAlex IEEE",
        "Crossref",
        "Crossref IEEE",
    ]

    for source_name, result in zip(source_names, results):
        if isinstance(result, Exception):
            print(f"[{source_name} Error] {result}")
        else:
            print(f"[{source_name}] Found {len(result)} papers")
            all_papers.extend(result)

    print(f"[ResearchX] Total candidates: {len(all_papers)}")

    unique_papers = remove_duplicate_papers(all_papers)

    IEEE_VENUE_KEYWORDS = (
        "ieee",
        "institute of electrical and electronics engineers",
        "ieeexplore",
        "transactions on",
        "ieee access",
        "ieee/cvf",
        "ieee/acm",
        "ieee transactions",
        "ieee journal",
        "ieee symposium",
        "ieee conference",
        "ieee international",
        "ieee letters",
    )

    for paper in unique_papers:
        venue = str(paper.get("venue") or "").lower()
        src = str(paper.get("source") or "").lower()
        url = str(paper.get("url") or "").lower()
        doi = str(paper.get("doi") or "").lower()

        is_ieee = (
            "ieee" in src
            or any(keyword in venue for keyword in IEEE_VENUE_KEYWORDS)
            or "ieee.org" in url
            or "10.1109/" in doi
        )
        paper["publication_type"] = "IEEE" if is_ieee else "Other"
        paper["is_ieee"] = is_ieee

    # Apply source filtering if requested
    if is_ieee_filter:
        unique_papers = [p for p in unique_papers if p.get("is_ieee") or p.get("publication_type") == "IEEE"]
        print(f"[ResearchX] Filtered for IEEE: {len(unique_papers)} papers remaining")
    elif source and source.lower() not in ("all", "any"):
        src_lower = source.lower()
        if "arxiv" in src_lower:
            unique_papers = [p for p in unique_papers if "arxiv" in str(p.get("source", "")).lower()]
        elif "semantic" in src_lower:
            unique_papers = [p for p in unique_papers if "semantic" in str(p.get("source", "")).lower()]
        elif "openalex" in src_lower:
            unique_papers = [p for p in unique_papers if "openalex" in str(p.get("source", "")).lower()]
        elif "crossref" in src_lower:
            unique_papers = [p for p in unique_papers if "crossref" in str(p.get("source", "")).lower()]

    print(f"[ResearchX] After duplicate removal & source filtering: {len(unique_papers)} papers")

    # Normalize all source-specific links
    normalized_papers = [
        normalize_paper_links(paper)
        for paper in unique_papers
    ]

    # Keep papers that have accessible links
    accessible_papers = [
        paper for paper in normalized_papers
        if has_accessible_link(paper)
    ]

    if not accessible_papers and normalized_papers:
        accessible_papers = normalized_papers

    print(f"[ResearchX] Accessible candidate papers: {len(accessible_papers)}")

    # Rerank candidate papers with Cohere
    reranked_papers = await rerank_papers(
        query,
        accessible_papers,
        top_n=len(accessible_papers)
    )

    RELEVANCE_THRESHOLD = 0.02
    strictly_relevant_papers = [
        paper
        for paper in reranked_papers
        if float(paper.get("relevance_score", 0.0)) >= RELEVANCE_THRESHOLD
    ]

    if not strictly_relevant_papers and reranked_papers:
        strictly_relevant_papers = reranked_papers

    print(f"[ResearchX] Strictly relevant papers: {len(strictly_relevant_papers)}")

    def get_year(paper):
        value = str(paper.get("published", "0"))
        match = re.search(r"\b(19|20)\d{2}\b", value)
        return int(match.group()) if match else 0

    def source_priority(paper):
        source_str = str(paper.get("source", "")).lower()
        if "ieee" in source_str or paper.get("is_ieee"):
            return 3
        if any(x in source_str for x in ["semantic scholar", "openalex", "crossref"]):
            return 2
        if "arxiv" in source_str:
            return 1
        return 0

    strictly_relevant_papers.sort(
        key=lambda paper: (
            paper.get("relevance_score", 0.0),
            get_year(paper),
            source_priority(paper),
            paper.get("citations", 0),
        ),
        reverse=True
    )

    final_papers = strictly_relevant_papers[:30]
    return final_papers


async def search_workspace_papers(
    query: str,
    limit: int = 10,
    sort_by: str = "relevance",
    year: str = "all",
    source: str = "all",
) -> List[Dict[str, Any]]:

    original_query = (query or "").strip()
    corrected_query = await correct_query_spelling(original_query)

    if not corrected_query:
        corrected_query = original_query

    print(f"[Workspace Search] Original query: '{original_query}'")
    print(f"[Workspace Search] Corrected query: '{corrected_query}'")

    papers = await search_all_sources(
        query=corrected_query,
        limit_per_source=30,
        source=source or "all",
    )

    # Comprehensive Year Filtering
    if year and year.lower() != "all":
        y_lower = year.lower().strip()
        if y_lower in ("foundational", "old", "<=2020"):
            papers = [p for p in papers if (p.get("year") or 0) <= 2020 and (p.get("year") or 0) > 0]
        elif y_lower in ("last_3_years", "recent_3", "2023-2026"):
            papers = [p for p in papers if (p.get("year") or 0) >= 2023]
        elif y_lower in ("last_5_years", "recent_5", "2021-2026"):
            papers = [p for p in papers if (p.get("year") or 0) >= 2021]
        elif y_lower in ("2025", "2026", "2025-2026"):
            papers = [p for p in papers if (p.get("year") or 0) >= 2025]
        elif "-" in y_lower:
            parts = y_lower.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start_y, end_y = int(parts[0]), int(parts[1])
                papers = [p for p in papers if start_y <= (p.get("year") or 0) <= end_y]
        elif y_lower.isdigit():
            target_year = int(y_lower)
            papers = [p for p in papers if p.get("year") == target_year]

    # Sorting
    if sort_by == "relevance":
        papers.sort(
            key=lambda p: (
                -(p.get("relevance_score") or 0.0),
                -(p.get("year") or 0),
                -(p.get("citations") or 0),
            )
        )
    elif sort_by == "year_desc":
        papers.sort(
            key=lambda p: (
                -(p.get("year") or 0),
                -(p.get("relevance_score") or 0.0),
                -(p.get("citations") or 0),
            )
        )
    elif sort_by == "year_asc":
        papers.sort(
            key=lambda p: (
                p.get("year") or 9999,
                -(p.get("relevance_score") or 0.0),
                -(p.get("citations") or 0),
            )
        )
    elif sort_by == "citations_desc":
        papers.sort(
            key=lambda p: (
                -(p.get("citations") or 0),
                -(p.get("relevance_score") or 0.0),
                -(p.get("year") or 0),
            )
        )

    # ----------------------------------------------------
    # Ensure Balanced Multi-Source & Guaranteed IEEE Papers
    # ----------------------------------------------------
    if (not source or source.lower() in ("all", "any", "global")) and papers:
        ieee_papers = [p for p in papers if p.get("is_ieee") or p.get("publication_type") == "IEEE"]
        other_papers = [p for p in papers if not (p.get("is_ieee") or p.get("publication_type") == "IEEE")]

        if ieee_papers:
            # Guarantee at least 1-2 IEEE papers in the top results
            num_ieee_to_include = min(2, len(ieee_papers))
            guaranteed_ieee = ieee_papers[:num_ieee_to_include]
            remaining_ieee = ieee_papers[num_ieee_to_include:]

            # Interleave guaranteed IEEE papers with top non-IEEE papers
            balanced_papers = []
            other_idx = 0
            ieee_idx = 0

            # Slot 1: Top paper (either top other or top IEEE)
            if other_papers:
                balanced_papers.append(other_papers[0])
                other_idx += 1

            # Slot 2: Guaranteed IEEE paper #1
            if ieee_idx < len(guaranteed_ieee):
                balanced_papers.append(guaranteed_ieee[ieee_idx])
                ieee_idx += 1

            # Slot 3: Next top other paper
            if other_idx < len(other_papers):
                balanced_papers.append(other_papers[other_idx])
                other_idx += 1

            # Slot 4: Guaranteed IEEE paper #2 (if available)
            if ieee_idx < len(guaranteed_ieee):
                balanced_papers.append(guaranteed_ieee[ieee_idx])
                ieee_idx += 1

            # Fill remaining slots from remaining other and IEEE papers
            remaining_pool = other_papers[other_idx:] + remaining_ieee
            # Re-sort remaining pool by chosen sort criteria
            if sort_by == "relevance":
                remaining_pool.sort(key=lambda p: -(p.get("relevance_score") or 0.0))
            elif sort_by == "year_desc":
                remaining_pool.sort(key=lambda p: -(p.get("year") or 0))
            elif sort_by == "citations_desc":
                remaining_pool.sort(key=lambda p: -(p.get("citations") or 0))

            balanced_papers.extend(remaining_pool)
            papers = balanced_papers

    # Attach query metadata to the papers for consumer introspection
    for p in papers:
        p["search_corrected_query"] = corrected_query
        p["search_original_query"] = original_query

    return papers[:limit]