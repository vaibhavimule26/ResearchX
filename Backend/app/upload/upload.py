from fastapi import APIRouter, UploadFile, File, HTTPException

from app.database.mongodb import papers_collection
from app.database.chroma import collection
from app.pdf.extractor import extract_text_from_pdf
from app.chunking.chunker import chunk_text
from app.embeddings.embedder import create_embeddings
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
async def upload_pdf(file: UploadFile = File(...)):

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
        # Store Vectors in ChromaDB
        # ==========================
        for i in range(len(chunks)):
            collection.add(
                ids=[
                    f"{file.filename}_{i}"
                ],
                documents=[
                    chunks[i]
                ],
                embeddings=[
                    embeddings[i]
                ],
                metadatas=[
                    {
                        "paper_name": file.filename,
                        "chunk_number": i,
                        "uploaded_at": uploaded_at
                    }
                ]
            )

        # ==========================
        # Store Document in MongoDB
        # ==========================
        result = papers_collection.insert_one(
            paper
        )

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

    for paper in papers_collection.find(
    {},
    {
        "_id": 0,
        "embeddings": 0,
        "text": 0,
        "chunks": 0
    }
):
     papers.append(paper)

    return success_response(
        message="Papers retrieved successfully",
        data={
            "papers": papers,
            "total": len(papers)
        }
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