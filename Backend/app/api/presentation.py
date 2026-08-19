import os
import tempfile

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.agents.ppt_agent import generate_presentation

router = APIRouter(
    prefix="/presentation",
    tags=["Presentation"],
)

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


class PresentationRequest(BaseModel):
    paper_name: str


@router.post("/generate")
def generate_presentation_text(
    request: PresentationRequest,
):

    try:

        query = (
            "complete research paper "
            "abstract methodology "
            "results datasets "
            "experiments conclusion"
        )

        embedding = model.encode(
            query
        ).tolist()

        results = collection.query(
            query_embeddings=[embedding],
            n_results=10,
            where={
                "paper_name": request.paper_name
            },
        )

        docs = results.get(
            "documents",
            [[]],
        )[0]

        if not docs:
            raise HTTPException(
                status_code=404,
                detail="Paper not found",
            )

        context = "\n\n".join(docs)

        presentation = generate_presentation(
            context
        )

        cache_dir = os.path.join(
            tempfile.gettempdir(),
            "researchx_cache",
        )

        os.makedirs(
            cache_dir,
            exist_ok=True,
        )

        cache_file = os.path.join(
            cache_dir,
            f"{request.paper_name}.txt",
        )

        with open(
            cache_file,
            "w",
            encoding="utf-8",
        ) as f:

            f.write(
                presentation
            )

        return {
            "success": True,
            "presentation": presentation,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )