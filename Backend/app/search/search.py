import os
import re
import json
import sqlite3
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.search.paper_search_service import search_all_sources


try:
    from app.agents.coordinator import run_agent
except ImportError:
    def run_agent(query: str, paper_name: Optional[str] = None):
        return f"Processed query: {query}"


router = APIRouter(prefix="", tags=["search"])


# ==========================================================
# DATABASE
# ==========================================================

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "database",
    "research.db"
)


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# CLEAN TEXT UTILITY
# ==========================================================

def extract_clean_text(raw_output) -> str:
    if not raw_output:
        return "No response generated."

    if isinstance(raw_output, dict):
        results = raw_output.get("results", {})

        if isinstance(results, dict):
            for key in [
                "gaps",
                "summary",
                "datasets",
                "experiments",
                "literature"
            ]:
                if (
                    key in results
                    and isinstance(results[key], dict)
                    and "output" in results[key]
                ):
                    return extract_clean_text(
                        results[key]["output"]
                    )

            for value in results.values():
                if isinstance(value, dict) and "output" in value:
                    return extract_clean_text(value["output"])

        for direct_key in [
            "output",
            "answer",
            "result",
            "text"
        ]:
            if direct_key in raw_output:
                return extract_clean_text(
                    raw_output[direct_key]
                )

    elif isinstance(raw_output, str):
        trimmed = raw_output.strip()

        if (
            trimmed.startswith("{")
            and trimmed.endswith("}")
        ) or (
            trimmed.startswith("[")
            and trimmed.endswith("]")
        ):
            try:
                clean_json_str = trimmed.replace("'", '"')
                parsed = json.loads(clean_json_str)
                return extract_clean_text(parsed)
            except Exception:
                pass

        match = re.search(
            r'["\']output["\']\s*:\s*["\']([\s\S]*?)["\']'
            r'\s*(?:,\s*["\']|\})',
            trimmed
        )

        if match and match.group(1):
            return (
                match.group(1)
                .replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\'", "'")
                .strip()
            )

        return trimmed

    return str(raw_output)


# ==========================================================
# REQUEST MODELS
# ==========================================================

class SearchRequest(BaseModel):
    query: Optional[str] = None
    session_id: Optional[str] = "default_session"
    paper_name: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    paper_name: Optional[str] = None


# ==========================================================
# A. MULTI-SOURCE PAPER SEARCH
# ==========================================================

@router.get("/search")
@router.post("/search")
async def handle_search_endpoint(
    request: Optional[SearchRequest] = None,
    query: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    search_query = (
        (request.query if request else None)
        or query
        or q
        or "Vision Transformers"
    )

    print(
        f"\n[ResearchX] Starting multi-source search: "
        f"{search_query}"
    )

    # Fetch papers from:
    # arXiv + Semantic Scholar + OpenAlex + Crossref
    papers = await search_all_sources(
        query=search_query,
        limit_per_source=30,
    )

    print(
        f"[ResearchX] Returning {len(papers)} total papers"
    )

    return {
        "status": "success",
        "query": search_query,
        "count": len(papers),
        "results": papers,
        "papers": papers,
        "data": {
            "papers": papers,
            "results": papers,
        },
    }


# ==========================================================
# B. AGENT Q&A
# ==========================================================

@router.post("/ask")
async def handle_ask(request: AskRequest):
    try:
        raw_agent_response = run_agent(
            query=request.question,
            paper_name=request.paper_name,
        )

        clean_answer = extract_clean_text(
            raw_agent_response
        )

        return {
            "status": "success",
            "data": {
                "answer": clean_answer,
                "paper_name": request.paper_name,
            },
            "answer": clean_answer,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


# ==========================================================
# C. CHAT SESSIONS
# ==========================================================

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

        cursor.execute(
            "SELECT * FROM chat_sessions "
            "ORDER BY updated_at DESC"
        )

        rows = cursor.fetchall()

        return {
            "status": "success",
            "data": {
                "sessions": [
                    dict(row)
                    for row in rows
                ]
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "sessions": []
            }
        }

    finally:
        if conn:
            conn.close()


# ==========================================================
# D. SEARCH HISTORY
# ==========================================================

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
            """
            SELECT * FROM search_history
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )

        rows = cursor.fetchall()

        return {
            "status": "success",
            "data": {
                "history": [
                    dict(row)
                    for row in rows
                ]
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "history": []
            }
        }

    finally:
        if conn:
            conn.close()