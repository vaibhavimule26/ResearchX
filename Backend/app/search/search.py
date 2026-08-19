import os
import re
import json
import sqlite3
import requests
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

try:
    from app.agents.coordinator import run_agent
except ImportError:
    # Fallback in case coordinator agent is located elsewhere
    def run_agent(query: str, paper_name: Optional[str] = None):
        return f"Processed query: {query}"

router = APIRouter(prefix="", tags=["search"])

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "research.db")


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================================================
# 1. DETERMINISTIC ACADEMIC PAPER FETCHING (arXiv & Semantic Scholar)
# ==============================================================================
def fetch_arxiv_papers(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Fetches verified preprints from arXiv API."""
    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        response = requests.get(url, timeout=8)
        papers = []
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip().replace("\n", " ")
                summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip().replace("\n", " ")
                published = entry.find("{http://www.w3.org/2005/Atom}published").text[:4]
                link = entry.find("{http://www.w3.org/2005/Atom}id").text
                
                authors = [a.find("{http://www.w3.org/2005/Atom}name").text for a in entry.findall("{http://www.w3.org/2005/Atom}author")]

                papers.append({
                    "title": title,
                    "abstract": summary,
                    "year": int(published) if published.isdigit() else 2024,
                    "url": link,
                    "source": "arXiv",
                    "authors": authors[:3],
                    "citations": 0
                })
        return papers
    except Exception as err:
        print(f"[arXiv API Error]: {err}")
        return []


def fetch_semantic_scholar_papers(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches peer-reviewed papers with real citation counts from Semantic Scholar."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields=title,abstract,year,url,citationCount,venue,authors"
        headers = {"User-Agent": "ResearchX-Platform/1.0"}
        response = requests.get(url, headers=headers, timeout=8)
        papers = []
        if response.status_code == 200:
            data = response.json()
            for p in data.get("data", []):
                if p.get("title"):
                    authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]
                    papers.append({
                        "title": p.get("title"),
                        "abstract": p.get("abstract") or "Abstract indexed in database.",
                        "year": p.get("year") or 2024,
                        "url": p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId')}",
                        "source": p.get("venue") or "Semantic Scholar",
                        "authors": authors[:3],
                        "citations": p.get("citationCount", 0)
                    })
        return papers
    except Exception as err:
        print(f"[Semantic Scholar API Error]: {err}")
        return []


def get_live_academic_papers(query: str) -> List[Dict[str, Any]]:
    """Deduplicates and sorts live academic papers."""
    arxiv = fetch_arxiv_papers(query, max_results=5)
    semantic = fetch_semantic_scholar_papers(query, limit=5)
    
    combined = arxiv + semantic
    unique_papers = []
    seen_titles = set()
    
    for paper in combined:
        normalized = re.sub(r'[^a-zA-Z0-9]', '', paper["title"]).lower()
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_papers.append(paper)
            
    # Sort latest first
    unique_papers.sort(key=lambda x: str(x.get("year", "0")), reverse=True)
    return unique_papers[:10]


# ==============================================================================
# 2. CLEAN TEXT UTILITY
# ==============================================================================
def extract_clean_text(raw_output) -> str:
    if not raw_output:
        return "No response generated."

    if isinstance(raw_output, dict):
        results = raw_output.get("results", {})
        if isinstance(results, dict):
            for key in ["gaps", "summary", "datasets", "experiments", "literature"]:
                if key in results and isinstance(results[key], dict) and "output" in results[key]:
                    return extract_clean_text(results[key]["output"])
            for v in results.values():
                if isinstance(v, dict) and "output" in v:
                    return extract_clean_text(v["output"])

        for direct_key in ["output", "answer", "result", "text"]:
            if direct_key in raw_output:
                return extract_clean_text(raw_output[direct_key])

    elif isinstance(raw_output, str):
        trimmed = raw_output.strip()
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
            try:
                clean_json_str = trimmed.replace("'", '"')
                parsed = json.loads(clean_json_str)
                return extract_clean_text(parsed)
            except Exception:
                pass

        m = re.search(r'["\']output["\']\s*:\s*["\']([\s\S]*?)["\']\s*(?:,\s*["\']|\})', trimmed)
        if m and m.group(1):
            return m.group(1).replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'").strip()

        return trimmed

    return str(raw_output)


# ==============================================================================
# 3. FASTAPI API ROUTE DEFINITIONS
# ==============================================================================
class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"
    paper_name: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    paper_name: Optional[str] = None


# --- A. Live Paper Discovery Route (Matches React UI Search) ---
@router.get("/search")
@router.post("/search")
async def handle_search_endpoint(
    request: Optional[SearchRequest] = None, 
    query: Optional[str] = Query(None),
    q: Optional[str] = Query(None)
):
    search_query = (request.query if request else None) or query or q or "Vision Transformers"
    
    # 1. Fetch live top-10 papers
    papers = get_live_academic_papers(search_query)
    
    # 2. Return payload in format consumed by React Frontend
    return {
        "status": "success",
        "query": search_query,
        "count": len(papers),
        "results": papers,
        "papers": papers,
        "data": {
            "papers": papers,
            "results": papers
        }
    }


# --- B. Agent Q&A Route (/ask) ---
@router.post("/ask")
async def handle_ask(request: AskRequest):
    try:
        raw_agent_response = run_agent(query=request.question, paper_name=request.paper_name)
        clean_answer = extract_clean_text(raw_agent_response)
        return {
            "status": "success",
            "data": {
                "answer": clean_answer,
                "paper_name": request.paper_name,
            },
            "answer": clean_answer
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- C. Chat Session & History Routes ---
@router.get("/sessions")
async def get_sessions():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT,
                paper_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return {"status": "success", "data": {"sessions": [dict(r) for r in rows]}}
    except Exception as e:
        return {"status": "error", "message": str(e), "data": {"sessions": []}}
    finally:
        if conn:
            conn.close()


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                query TEXT,
                answer TEXT,
                paper_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            "SELECT * FROM search_history WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        return {"status": "success", "data": {"history": [dict(r) for r in rows]}}
    except Exception as e:
        return {"status": "error", "message": str(e), "data": {"history": []}}
    finally:
        if conn:
            conn.close()