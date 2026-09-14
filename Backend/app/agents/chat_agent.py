import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

try:
    import pymupdf
except ImportError:
    pymupdf = None

from app.rag.embeddings import create_query_embedding
from app.rag.retriever import retrieve_chunks, index_paper
from app.database.mongodb import papers_collection
from app.llm.multi_api_router import (
    call_groq_api,
    call_cohere_api,
    call_mistral_api,
    call_gemini_api,
)

# SQLite database path
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


def init_chat_tables():
    """Ensure chat_sessions and search_history tables exist."""
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
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ChatAgent] Init tables error: {e}")


# Initialize tables on load
init_chat_tables()


# ==========================================================
# Locate PDF on Disk
# ==========================================================
def find_pdf_on_disk(paper_name: str) -> Optional[str]:
    """Find the local path for an uploaded PDF."""
    if not paper_name:
        return None

    clean_name = os.path.basename(paper_name.strip())
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.dirname(app_dir)
    workspace_dir = os.path.dirname(backend_dir)

    candidate_paths = [
        os.path.join(backend_dir, "uploads", clean_name),
        os.path.join(backend_dir, "uploads", paper_name),
        os.path.join(workspace_dir, "uploads", clean_name),
        os.path.join(workspace_dir, "uploads", paper_name),
        os.path.join(workspace_dir, "Backend", "uploads", clean_name),
        os.path.join(os.getcwd(), "uploads", clean_name),
        os.path.join(os.getcwd(), "Backend", "uploads", clean_name),
    ]

    for p in candidate_paths:
        if os.path.exists(p) and os.path.isfile(p):
            return p

    for upload_folder in [
        os.path.join(backend_dir, "uploads"),
        os.path.join(workspace_dir, "uploads"),
    ]:
        if os.path.exists(upload_folder):
            for fname in os.listdir(upload_folder):
                if fname.lower() == clean_name.lower():
                    return os.path.join(upload_folder, fname)

    return None


# ==========================================================
# Page & Section Detector
# ==========================================================
def find_page_and_section(
    paper_name: str,
    snippet: str,
) -> Tuple[Optional[int], Optional[str]]:
    """Determine the PDF page number and section heading for a chunk."""
    if not pymupdf or not paper_name or not snippet:
        return None, None

    pdf_path = find_pdf_on_disk(paper_name)
    if not pdf_path:
        return None, None

    clean_snippet = " ".join(snippet.split())
    words = clean_snippet.split()
    search_terms = []
    if len(words) >= 6:
        search_terms.append(" ".join(words[:8]).lower())
        search_terms.append(" ".join(words[len(words)//2 : len(words)//2 + 8]).lower())
        search_terms.append(" ".join(words[-8:]).lower())
    else:
        search_terms.append(clean_snippet.lower()[:50])

    try:
        doc = pymupdf.open(pdf_path)
        for page_idx, page in enumerate(doc, start=1):
            page_text = page.get_text().lower()
            for term in search_terms:
                if term and term in page_text:
                    section = detect_section_from_text(page.get_text())
                    doc.close()
                    return page_idx, section
        doc.close()
    except Exception as e:
        print(f"[ChatAgent] Page detection error for {paper_name}: {e}")

    return None, None


def detect_section_from_text(text: str) -> Optional[str]:
    """Detect section heading from text."""
    if not text:
        return None

    headings = [
        "Abstract",
        "Introduction",
        "Related Work",
        "Background",
        "Literature Review",
        "Methodology",
        "Proposed Method",
        "System Architecture",
        "Architecture",
        "Experimental Setup",
        "Experiments",
        "Results and Discussion",
        "Results",
        "Discussion",
        "Evaluation",
        "Limitations",
        "Future Scope",
        "Future Work",
        "Conclusion",
        "References",
    ]

    for h in headings:
        pattern = rf"(?i)(?:\b\d+\.?\s*)?({re.escape(h)})\b"
        if re.search(pattern, text[:1500]):
            return h

    return None


# ==========================================================
# Clean Conversational Response Post-Processor
# ==========================================================
def clean_conversational_response(text: str) -> str:
    """
    Sanitize raw LLM generation:
    - Removes awkward inline citations (e.g. 【Evidence 1】, (Evidence 1, p. 2))
    - Removes robotic preambles and meta-headers like:
      '**Why NLP is important – evidence-based points**' or 'Evidence-based points:'
    - Preserves clean Markdown formatting (bold, bullets, headings, tables).
    """
    if not text:
        return "I couldn't find this information in the uploaded paper."

    cleaned = text.strip()

    # 1. Strip bracketed / parenthetical in-text evidence tags
    cleaned = re.sub(r"【\s*Evidence\s*\d+\s*】", "", cleaned)
    cleaned = re.sub(r"\[\s*Evidence\s*\d+[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*(?:see\s+)?Evidence\s*\d+[^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*p\.\s*\d+,\s*Evidence\s*\d+[^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(\s*Page\s*\d+[^)]*\)", "", cleaned, flags=re.IGNORECASE)

    # 2. Strip robotic meta-headers like:
    # **Why Natural Language Processing (NLP) is important – evidence-based points**
    cleaned = re.sub(
        r"^\s*#*\s*\*\*[^\n*]+[–\-—]\s*(?:evidence-based points|key points|evidence points)\*\*\s*\n*",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    # Strip opening preambles like "According to the evidence...", "Based on the provided paper..."
    cleaned = re.sub(
        r"^\s*#*\s*(?:Here are (?:some )?evidence-based points|Evidence-based points|ResearchX AI analysis|According to the (?:provided )?evidence|Based on the (?:provided )?(?:paper|evidence)[^:\n]*):\s*\n*",
        "",
        cleaned,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # 3. Clean up any double spaces left before punctuation or within lines
    cleaned = re.sub(r"[ \t]+([.,;?!])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 4. Standardize out-of-scope fallback phrasing if information is absent
    if (
        re.search(r"couldn'?t find (?:any|this) (?:information|statement|mention|detail)", cleaned, re.IGNORECASE)
        or re.search(r"(?:not mentioned|not discussed|not found) in the (?:uploaded )?paper", cleaned, re.IGNORECASE)
    ) and len(cleaned) < 220:
        return "I couldn't find this information in the uploaded paper."

    return cleaned.strip()


# ==========================================================
# Ensure Paper Indexed in ChromaDB
# ==========================================================
def ensure_paper_indexed(paper_name: str) -> bool:
    """If paper is in MongoDB or disk but not yet indexed in ChromaDB, index it."""
    try:
        mongo_paper = (
            papers_collection.find_one({"filename": paper_name})
            or papers_collection.find_one({"title": paper_name})
        )

        if mongo_paper:
            chunks = mongo_paper.get("chunks") or []
            embeddings = mongo_paper.get("embeddings") or []

            if chunks and embeddings and len(chunks) == len(embeddings):
                index_paper(
                    paper_id=paper_name,
                    chunks=chunks,
                    embeddings=embeddings,
                    metadata={
                        "paper_name": paper_name,
                        "title": mongo_paper.get("title") or paper_name,
                        "uploaded_at": mongo_paper.get("uploaded_at") or "",
                    },
                )
                print(f"[ChatAgent] Re-indexed {len(chunks)} chunks into ChromaDB for {paper_name}")
                return True

        pdf_path = find_pdf_on_disk(paper_name)
        if pdf_path and pymupdf:
            from app.pdf.extractor import extract_text_from_pdf
            from app.chunking.chunker import chunk_text
            from app.embeddings.embedder import create_embeddings

            text = extract_text_from_pdf(pdf_path)
            if text and text.strip():
                chunks = chunk_text(text)
                if chunks:
                    embeddings = create_embeddings(chunks)
                    index_paper(
                        paper_id=paper_name,
                        chunks=chunks,
                        embeddings=embeddings,
                        metadata={"paper_name": paper_name, "title": paper_name},
                    )
                    print(f"[ChatAgent] Indexed {len(chunks)} chunks from disk for {paper_name}")
                    return True
    except Exception as e:
        print(f"[ChatAgent] Ensure paper indexed error: {e}")

    return False


# ==========================================================
# Retrieve Conversation History
# ==========================================================
def get_session_history(session_id: str, limit: int = 6) -> List[Dict[str, str]]:
    """Fetch previous turns for the session from SQLite."""
    history: List[Dict[str, str]] = []
    if not session_id:
        return history

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT query, answer FROM search_history
            WHERE session_id = ? AND query IS NOT NULL AND query != ''
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        for row in reversed(rows):
            q = row["query"]
            a = row["answer"]
            if q:
                history.append({"role": "user", "content": q})
            if a:
                history.append({"role": "assistant", "content": a})
    except Exception as e:
        print(f"[ChatAgent] History fetch error: {e}")

    return history


# ==========================================================
# Main Chat Agent Function
# ==========================================================
def chat_with_paper(
    query: str,
    paper_name: Optional[str] = None,
    session_id: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    RAG-grounded AI chat agent specifically connected to the user's uploaded paper.
    Retrieves evidence from ChromaDB, formats natural conversational responses,
    and returns clean source citations separately.
    """
    if not query or not query.strip():
        return {
            "answer": "Please ask a question about the uploaded research paper.",
            "sources": [],
            "paper_name": paper_name,
            "session_id": session_id or "default_session",
        }

    clean_query = query.strip()
    session_id = session_id or f"chat_{int(os.times().system * 1000)}"

    # 1. Verify paper selection
    if not paper_name or not paper_name.strip():
        return {
            "answer": "No research paper selected. Upload or select a PDF to start document-based chat.",
            "sources": [],
            "paper_name": None,
            "session_id": session_id,
        }

    clean_paper_name = paper_name.strip()

    # 2. Retrieve relevant chunks from ChromaDB
    query_embedding = create_query_embedding(clean_query)
    retrieved_chunks = []

    if query_embedding:
        try:
            retrieved_chunks = retrieve_chunks(
                query_embedding=query_embedding,
                paper_id=clean_paper_name,
                top_k=6,
            )
        except Exception as e:
            print(f"[ChatAgent] ChromaDB retrieval error: {e}")

    if not retrieved_chunks:
        indexed = ensure_paper_indexed(clean_paper_name)
        if indexed and query_embedding:
            try:
                retrieved_chunks = retrieve_chunks(
                    query_embedding=query_embedding,
                    paper_id=clean_paper_name,
                    top_k=6,
                )
            except Exception as e:
                print(f"[ChatAgent] ChromaDB retry error: {e}")

    # Fallback to MongoDB text if vector retrieval failed
    mongo_context = ""
    if not retrieved_chunks:
        try:
            mongo_paper = papers_collection.find_one(
                {"filename": clean_paper_name}
            ) or papers_collection.find_one({"title": clean_paper_name})
            if mongo_paper:
                mongo_text = mongo_paper.get("text", "")
                if mongo_text:
                    mongo_context = mongo_text[:8000]
                    retrieved_chunks = [
                        {
                            "text": mongo_context,
                            "metadata": {
                                "paper_name": clean_paper_name,
                                "chunk_index": 0,
                                "page": 1,
                            },
                            "distance": 0.0,
                        }
                    ]
        except Exception as e:
            print(f"[ChatAgent] MongoDB fallback error: {e}")

    if not retrieved_chunks and not mongo_context:
        answer = "I couldn't find this information in the uploaded paper."
        save_chat_interaction(session_id, clean_query, answer, clean_paper_name)
        return {
            "answer": answer,
            "sources": [],
            "paper_name": clean_paper_name,
            "session_id": session_id,
        }

    # 3. Build Source References & Evidence Blocks
    sources = []
    evidence_blocks = []

    for i, ch in enumerate(retrieved_chunks, start=1):
        chunk_text = ch.get("text", "").strip()
        meta = ch.get("metadata", {}) or {}
        chunk_idx = meta.get("chunk_index", meta.get("chunk_number", i - 1))

        page_num = meta.get("page")
        section = meta.get("section")
        if not page_num or not section:
            p_found, s_found = find_page_and_section(clean_paper_name, chunk_text)
            page_num = page_num or p_found
            section = section or s_found

        source_info = {
            "chunk_index": int(chunk_idx) if str(chunk_idx).isdigit() else i - 1,
            "page": page_num if page_num else (i if i <= 3 else None),
            "section": section or "Paper Content",
            "snippet": chunk_text[:280] + ("..." if len(chunk_text) > 280 else ""),
            "distance": round(ch.get("distance", 0.0), 3),
        }
        sources.append(source_info)

        loc_label = f"Evidence {i}"
        if source_info["page"]:
            loc_label += f" | Page {source_info['page']}"
        if source_info["section"] and source_info["section"] != "Paper Content":
            loc_label += f" | {source_info['section']}"

        evidence_blocks.append(f"[{loc_label}]\n{chunk_text}")

    evidence_text = "\n\n---\n\n".join(evidence_blocks)

    # 4. Fetch Multi-Turn Memory
    if history is None:
        history = get_session_history(session_id, limit=4)

    history_text = ""
    if history:
        turns = []
        for turn in history:
            role = "Researcher" if turn["role"] == "user" else "ResearchX"
            turns.append(f"{role}: {turn['content']}")
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n\n"

    # 5. Formulate Prompt for Natural, Direct, Scholarly AI Response
    system_instructions = (
        "You are ResearchX AI, an expert, conversational academic research assistant. "
        f"You have thoroughly analyzed the researcher's uploaded paper: '{clean_paper_name}'.\n\n"
        "CORE CONVERSATIONAL PRINCIPLES:\n"
        "1. ANSWER THE QUESTION DIRECTLY FIRST:\n"
        "   - Start immediately with a natural, direct answer to the user's question.\n"
        "   - Do NOT begin with unnecessary meta-headers like '**Why [Topic] is important – evidence-based points**' or preambles like 'According to the evidence...' or 'Here are some points...'.\n"
        "   - The tone must feel like a knowledgeable, scholarly AI research colleague (similar to ChatGPT or Claude discussing a paper).\n\n"
        "2. ADAPTIVE ANSWER STRUCTURE:\n"
        "   - Simple or factual question: Provide a clear, direct 2 to 4 sentence answer.\n"
        "   - Detailed question: Provide a direct opening answer, followed by clear, organized bullet points with bold key terms.\n"
        "   - Methodology question: Provide an overview paragraph, sequential methodology steps, and key parameters or architecture details.\n"
        "   - Comparison question: Synthesize comparison into a clean Markdown table (| Method / Aspect | Proposed Approach | Baseline / Comparison |) followed by key trade-offs.\n"
        "   - Summary question: Structured overview covering background, main contributions, methodology, empirical findings, and limitations.\n\n"
        "3. CLEAN CITATIONS — NO INLINE CLUTTER:\n"
        "   - Do NOT insert clumsy in-text citations like '【Evidence 1】', '(Evidence 1, p. 1)', or '[Evidence 2]' inside sentences. The user interface will display verified source pages and sections separately below your answer.\n\n"
        "4. STRICT ACCURACY & ZERO HALLUCINATION:\n"
        "   - Ground your answer strictly in the paper excerpts provided in the EVIDENCE section.\n"
        "   - Do NOT fabricate findings, benchmarks, datasets, or claims not present in the paper.\n"
        "   - If the requested information cannot be found or concluded from the paper, state clearly and naturally:\n"
        '     "I couldn\'t find this information in the uploaded paper."\n\n'
        "5. BEAUTIFUL MARKDOWN FORMATTING:\n"
        "   - Use clean Markdown: bullet lists, numbered lists, bold text for key terms, code blocks for code/formulas, and clean tables for comparisons.\n"
        "   - Avoid repetitive phrasing or circular definitions."
    )

    user_prompt = (
        f"{history_text}"
        f"RESEARCH PAPER: '{clean_paper_name}'\n\n"
        f"EVIDENCE FROM PAPER:\n"
        f"{evidence_text}\n\n"
        f"RESEARCHER'S QUESTION:\n"
        f"{clean_query}\n\n"
        "Provide a direct, natural, and well-structured answer based strictly on the paper evidence above:"
    )

    # 6. Call LLM Router with high-speed failover
    raw_answer = ""
    try:
        raw_answer = call_groq_api(prompt=user_prompt, context=system_instructions)
    except Exception as e:
        print(f"[ChatAgent] Groq call error: {e}")

    if not raw_answer or "failed" in raw_answer.lower() or len(raw_answer.strip()) < 10:
        try:
            raw_answer = call_gemini_api(prompt=user_prompt, context=system_instructions)
        except Exception as e:
            print(f"[ChatAgent] Gemini call error: {e}")

    if not raw_answer or "failed" in raw_answer.lower() or len(raw_answer.strip()) < 10:
        try:
            raw_answer = call_mistral_api(prompt=user_prompt, context=system_instructions)
        except Exception as e:
            print(f"[ChatAgent] Mistral call error: {e}")

    if not raw_answer or "failed" in raw_answer.lower() or len(raw_answer.strip()) < 10:
        try:
            raw_answer = call_cohere_api(prompt=user_prompt, context=system_instructions)
        except Exception as e:
            print(f"[ChatAgent] Cohere call error: {e}")

    # Clean the generated answer using the conversational post-processor
    final_answer = clean_conversational_response(raw_answer)

    # 7. Persistence: Save interaction to SQLite
    save_chat_interaction(session_id, clean_query, final_answer, clean_paper_name)

    return {
        "answer": final_answer,
        "sources": sources,
        "paper_name": clean_paper_name,
        "session_id": session_id,
    }


def save_chat_interaction(
    session_id: str,
    query: str,
    answer: str,
    paper_name: Optional[str],
):
    """Record turn in search_history and upsert chat_sessions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO search_history (session_id, query, answer, paper_name)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, query, answer, paper_name),
        )

        title = query[:45].strip()
        if len(query) > 45:
            title += "..."

        cursor.execute(
            """
            INSERT INTO chat_sessions (session_id, title, paper_name, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                paper_name = excluded.paper_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session_id, title, paper_name),
        )

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ChatAgent] Save interaction error: {e}")
