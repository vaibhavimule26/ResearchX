from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from app.auth.jwt_handler import get_optional_user
from app.services.activity_service import log_user_activity

from app.database.mongodb import papers_collection
from app.database.chroma import collection
from app.pdf.extractor import extract_text_from_pdf
from app.chunking.chunker import chunk_text
from app.embeddings.embedder import create_embeddings
from app.rag.retriever import index_paper
from app.rag.rag_service import clear_rag_cache
from app.agents.coordinator import clear_context_cache
from app.services.plagiarism_service import clear_plagiarism_cache
from app.utils.response import success_response

import shutil
import os
from datetime import datetime

router = APIRouter()

UPLOAD_FOLDER = "uploads"


# ==========================
# Upload PDF
# ==========================
@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), request: Request = None):


    # Validate PDF file
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Check duplicate paper
    existing_paper = papers_collection.find_one(
        {"filename": file.filename}
    )

    if existing_paper:
        raise HTTPException(
            status_code=409,
            detail="A paper with this filename already exists"
        )

    # Create uploads folder
    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    # Create file path
    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    try:
        # ==========================
        # Save Uploaded PDF
        # ==========================
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        # ==========================
        # Extract PDF Text
        # ==========================
        text = extract_text_from_pdf(
            file_path
        )

        # Validate extracted text
        if not text or not text.strip():
            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text found in PDF. "
                    "The PDF may be empty or image-based."
                )
            )

        # ==========================
        # Split Text Into Chunks
        # ==========================
        chunks = chunk_text(text)

        if not chunks:
            if os.path.exists(file_path):
                os.remove(file_path)

            raise HTTPException(
                status_code=400,
                detail="Could not create chunks from PDF"
            )

        # ==========================
        # Create Embeddings
        # ==========================
        embeddings = create_embeddings(
            chunks
        )

        uploaded_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ==========================
        # MongoDB Document
        # ==========================
        paper = {
            "title": file.filename,
            "filename": file.filename,
            "filepath": file_path,
            "text": text,
            "chunks": chunks,
            "embeddings": embeddings,
            "uploaded_at": uploaded_at
        }

        # ==========================
        # Store Vectors in ChromaDB (Batch)
        # ==========================
        chunk_ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
        chunk_metadatas = [
            {
                "paper_name": file.filename,
                "chunk_number": i,
                "uploaded_at": uploaded_at,
            }
            for i in range(len(chunks))
        ]
        collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
        )

        # ==========================
        # RAG ChromaDB Index (Reuse embeddings)
        # ==========================
        index_paper(
            paper_id=file.filename,
            chunks=chunks,
            embeddings=embeddings,
            metadata={
                "paper_name": file.filename,
                "title": file.filename,
                "uploaded_at": uploaded_at,
            },
        )

        # ==========================
        # Store Document in MongoDB
        # ==========================
        result = papers_collection.insert_one(
            paper
        )

        # Log activity if user is authenticated
        try:
            user = get_optional_user(request)
            if user:
                log_user_activity(
                    user_id=user["user_id"],
                    user_email=user["email"],
                    action_name="PDF Uploaded",
                    activity_type="upload",
                    topic=None,
                    paper_name=file.filename,
                    agent="Document Ingestion",
                    status="Completed",
                    details=f"Uploaded {file.filename} ({len(chunks)} chunks indexed)",
                )
        except Exception as act_err:
            print(f"[Upload Activity Log Error]: {act_err}")

        # Invalidate in-memory caches
        clear_context_cache()
        clear_rag_cache()
        clear_plagiarism_cache()


        return success_response(
            message="PDF uploaded successfully",
            data={
                "filename": file.filename,
                "paper_id": str(result.inserted_id),
                "characters": len(text),
                "chunks": len(chunks)
            }
        )
    except HTTPException:
        raise

    except Exception as error:
        # Remove local file if upload fails
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"PDF upload failed: {str(error)}"
        )


# ==========================
# Get All Uploaded Papers
# ==========================
@router.get("/papers")
async def get_papers():

    papers = []

    # Query all papers and ensure uploaded ones come first
    raw_papers = list(
        papers_collection.find(
            {},
            {
                "embeddings": 0,
                "text": 0,
                "chunks": 0
            }
        ).sort("uploaded_at", -1)
    )

    for paper in raw_papers:
        if "_id" in paper:
            doc_id = str(paper["_id"])
            paper["id"] = doc_id
            paper["paper_id"] = doc_id
            del paper["_id"]

        # Guarantee filename is present
        if not paper.get("filename"):
            paper["filename"] = paper.get("title") or "Untitled Paper"
        papers.append(paper)

    return success_response(
        message="Papers retrieved successfully",
        data={
            "papers": papers,
            "total": len(papers)
        }
    )


# ==========================
# Download PDF
# ==========================
@router.get("/papers/{filename}")
async def download_paper(filename: str):

    paper = papers_collection.find_one(
        {"filename": filename}
    )

    if not paper:
        raise HTTPException(
            status_code=404,
            detail="Paper not found"
        )

    file_path = paper.get("filepath")

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
    )


# ==========================
# Delete Uploaded Paper
# ==========================
@router.delete("/papers/{filename}")
async def delete_paper(filename: str):

    # Find paper in MongoDB
    paper = papers_collection.find_one(
        {"filename": filename}
    )

    if not paper:
        raise HTTPException(
            status_code=404,
            detail="Paper not found"
        )

    try:
        # ==========================
        # Delete New ChromaDB Chunks
        # metadata: paper_name
        # ==========================
        collection.delete(
            where={
                "paper_name": filename
            }
        )

        # ==========================
        # Delete Older ChromaDB Chunks
        # metadata: filename
        # ==========================
        collection.delete(
            where={
                "filename": filename
            }
        )

        # ==========================
        # Delete From MongoDB
        # ==========================
        papers_collection.delete_many(
            {"filename": filename}
        )

        # ==========================
        # Delete Local PDF
        # ==========================
        file_path = paper.get(
            "filepath"
        )

        if (
            file_path
            and os.path.exists(file_path)
        ):
            os.remove(file_path)

        clear_context_cache()
        clear_rag_cache()
        clear_plagiarism_cache()

        return success_response(
            message="Paper deleted successfully",
            data={
                "filename": filename
            }
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete paper: {str(error)}"
        )