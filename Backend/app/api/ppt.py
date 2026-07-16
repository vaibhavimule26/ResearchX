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

        # ----------------------------------------
        # Retrieve Paper Context
        # ----------------------------------------
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

        # ----------------------------------------
        # Cache Directory
        # ----------------------------------------
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

        # ----------------------------------------
        # Load Cached Presentation
        # ----------------------------------------
        if os.path.exists(cache_file):

            with open(
                cache_file,
                "r",
                encoding="utf-8",
            ) as f:

                presentation = f.read()

        else:

            presentation = generate_presentation(
                context
            )

            with open(
                cache_file,
                "w",
                encoding="utf-8",
            ) as f:

                f.write(
                    presentation
                )

        # ----------------------------------------
        # Generate PPTX
        # ----------------------------------------
        output_file = os.path.join(
            tempfile.gettempdir(),
            "ResearchX_Presentation.pptx",
        )

        create_ppt(
            presentation,
            output_file,
        )

        # ----------------------------------------
        # Return PPT
        # ----------------------------------------
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