import os
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from app.database.chroma import collection
from app.agents.ppt_agent import generate_presentation
from app.utils.ppt_export import create_ppt


router = APIRouter(
    prefix="/ppt",
    tags=["PowerPoint"],
)

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


class PPTRequest(BaseModel):
    paper_name: str


@router.post("/generate")
def generate_ppt(
    request: PPTRequest,
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

        output_file = os.path.join(
            tempfile.gettempdir(),
            "ResearchX_Presentation.pptx",
        )

        create_ppt(
            presentation,
            output_file,
        )

        return FileResponse(
            output_file,
            filename="ResearchX_Presentation.pptx",
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )