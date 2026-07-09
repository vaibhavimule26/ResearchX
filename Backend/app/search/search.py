from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.database.mongodb import search_history_collection
from app.llm.gemini import generate_answer
from app.agents.coordinator import run_agent
from app.utils.response import success_response

router = APIRouter()

# Load embedding model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )

    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=100
    )

    paper_name: str | None = Field(
        default=None,
        max_length=255
    )
@router.post("/search")
async def search(request: SearchRequest):


       # ==========================
    # Generate Query Embedding
    # ==========================
    query_embedding = model.encode(
        request.query
    ).tolist()

        # ==========================
    # Retrieve Similar Chunks
    # ==========================
    if request.paper_name:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=6,
            where={
                "paper_name": request.paper_name
            }
        )
    else:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=6
        )




    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # ==========================
    # No Paper Found
    # ==========================
    if not documents:
        return {
            "question": request.query,
            "session_id": request.session_id,
            "answer": (
                "No matching research paper was found. "
                "Please upload a PDF or check the paper name."
            )
        }

    # ==========================
    # RAG Context
    # ==========================
    context = "\n\n".join(documents)

    # ==========================
    # Conversation Memory
    # ==========================
    previous_messages = list(
        search_history_collection.find(
            {
                "session_id": request.session_id
            },
            {
                "_id": 0,
                "query": 1,
                "answer": 1
            }
        )
        .sort("_id", -1)
        .limit(3)
    )

    previous_messages.reverse()

    conversation_history = ""

    for message in previous_messages:
        conversation_history += (
            f"\nUser: {message.get('query', '')}\n"
            f"Assistant: {message.get('answer', '')}\n"
        )
    if conversation_history:
        context = (
            f"Previous Conversation:\n"
            f"{conversation_history}\n\n"
            f"Retrieved Research Paper Context:\n"
            f"{context}"
        )

    # ==========================
    # Paper Comparison
    # ==========================
    if (
        "compare" in request.query.lower()
        or "comparison" in request.query.lower()
    ):
        paper = collection.get()

        all_documents = paper.get("documents", [])
        all_metadatas = paper.get("metadatas", [])

        comparison_context = ""

        for i in range(len(all_documents)):
            metadata = (
                all_metadatas[i]
                if i < len(all_metadatas)
                and all_metadatas[i]
                else {}
            )

            filename = (
                metadata.get("paper_name")
                or metadata.get("filename")
                or f"Paper {i + 1}"
            )

            comparison_context += (
                f"\n\n"
                f"=====================================\n"
                f"Paper {i + 1}: {filename}\n"
                f"=====================================\n\n"
                f"{all_documents[i]}"
            )

        if conversation_history:
            comparison_context = (
                f"Previous Conversation:\n"
                f"{conversation_history}\n\n"
                f"Uploaded Research Papers:\n"
                f"{comparison_context}"
            )

        answer = run_agent(
            request.query,
            comparison_context
        )

    else:
        answer = run_agent(
            request.query,
            context
        )



    # ==========================
    # Specialized Agent Response
    # ==========================
    if answer is not None:
        search_history_collection.insert_one(
    {
        "session_id": request.session_id,
        "paper_name": request.paper_name,
        "query": request.query,
        "answer": answer,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
)
        return success_response(
    message="Search completed successfully",
    data={
        "question": request.query,
        "session_id": request.session_id,
        "paper_name": request.paper_name,
        "answer": answer,
        "papers": metadatas
    }
)
    # ==========================
    # Default RAG Question Answering
    # ==========================
    answer = generate_answer(
        context,
        request.query
    )

    # ==========================
    # Save Search History
    # ==========================
    search_history_collection.insert_one(
    {
        "session_id": request.session_id,
        "paper_name": request.paper_name,
        "query": request.query,
        "answer": answer,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
)

    return success_response(
    message="Search completed successfully",
    data={
        "question": request.query,
        "session_id": request.session_id,
        "paper_name": request.paper_name,
        "answer": answer,
        "sources": documents,
        "papers": metadatas
    }
)

# ==========================
# Get Search History by Session
# ==========================
@router.get("/search-history/{session_id}")
async def get_search_history(session_id: str):

    history = []

    cursor = search_history_collection.find(
        {
            "session_id": session_id
        },
        {
            "_id": 0
        }
    ).sort("created_at", 1)

    for item in cursor:
        history.append(item)

    return success_response(
    message="Search history retrieved successfully",
    data={
        "session_id": session_id,
        "history": history,
        "total": len(history)
    }
)


# ==========================
# Delete Search History by Session
# ==========================
@router.delete("/search-history/{session_id}")
async def delete_search_history(session_id: str):

    result = search_history_collection.delete_many(
        {
            "session_id": session_id
        }
    )

    return success_response(
        message="Conversation history deleted successfully",
        data={
            "session_id": session_id,
            "deleted_messages": result.deleted_count
        }
    )


# ==========================
# Get All Conversation Sessions
# ==========================
@router.get("/sessions")
async def get_sessions():

    session_ids = search_history_collection.distinct(
        "session_id"
    )

    sessions = []

    for session_id in session_ids:

        # First message of session
        first_message = search_history_collection.find_one(
            {
                "session_id": session_id
            },
            {
                "_id": 0,
                "query": 1,
                "paper_name": 1,
                "created_at": 1
            },
            sort=[
                ("created_at", 1)
            ]
        )

        # Latest message of session
        latest_message = search_history_collection.find_one(
            {
                "session_id": session_id
            },
            {
                "_id": 0,
                "created_at": 1
            },
            sort=[
                ("created_at", -1)
            ]
        )

        if first_message:
            sessions.append(
                {
                    "session_id": session_id,
                    "title": first_message.get(
                        "query",
                        "New Chat"
                    ),
                    "paper_name": first_message.get(
                        "paper_name"
                    ),
                    "created_at": first_message.get(
                        "created_at"
                    ),
                    "updated_at": (
                        latest_message.get("created_at")
                        if latest_message
                        else first_message.get("created_at")
                    )
                }
            )

    # Latest active session first
    sessions.sort(
        key=lambda session: (
            session.get("updated_at") or ""
        ),
        reverse=True
    )

    return success_response(
    message="Sessions retrieved successfully",
    data={
        "sessions": sessions,
        "total": len(sessions)
    }
)
