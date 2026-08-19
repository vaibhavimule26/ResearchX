import os
import re
import json
import sqlite3
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.coordinator import run_agent

router = APIRouter(prefix="", tags=["search"])

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "research.db")


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_clean_text(raw_output) -> str:
    """Strictly extract clean plain text markdown from dictionary or string."""
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


def search_paper(query: str, session_id: str, paper_name: Optional[str] = None):
    try:
        raw_agent_response = run_agent(query=query, paper_name=paper_name)
        clean_answer = extract_clean_text(raw_agent_response)

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
                """
                INSERT INTO search_history (session_id, query, answer, paper_name)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, query, clean_answer, paper_name),
            )

            title = query[:45] + "..." if len(query) > 45 else query
            cursor.execute(
                """
                INSERT INTO chat_sessions (session_id, title, paper_name)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
                """,
                (session_id, title, paper_name),
            )

            conn.commit()
        except Exception as db_err:
            print(f"[Database Error]: {db_err}")
        finally:
            if conn:
                conn.close()

        return {
            "status": "success",
            "data": {
                "answer": clean_answer,
                "paper_name": paper_name,
                "session_id": session_id,
            },
            "result": clean_answer,
            "answer": clean_answer,
        }

    except Exception as e:
        print(f"Error in search_paper: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": {
                "answer": f"Unable to process query: {str(e)}",
                "paper_name": paper_name,
                "session_id": session_id,
            },
        }


class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"
    paper_name: Optional[str] = None


class AskRequest(BaseModel):
    question: str
    paper_name: Optional[str] = None


@router.post("/search")
async def handle_search(request: SearchRequest):
    return search_paper(request.query, request.session_id, request.paper_name)


@router.post("/ask")
async def handle_ask(request: AskRequest):
    return search_paper(request.question, "ask_session", request.paper_name)


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