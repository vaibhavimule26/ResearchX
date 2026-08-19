import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables FIRST
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

# ==========================================================
# FastAPI & Middleware Imports
# ==========================================================
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# ==========================================================
# Application & Router Imports
# ==========================================================
from app.utils.response import success_response
from app.api.routes import router
from app.upload.upload import router as upload_router
from app.search.search import router as search_router
from app.api.analysis import router as analysis_router
from app.api.report import router as report_router
from app.api.ppt import router as ppt_router
from app.api.presentation import router as presentation_router
from app.api.dashboard import router as dashboard_router
from app.api.paper_search import router as paper_search_router

# Multi-Agent Coordinator & Generator Services
from app.agents.coordinator import run_agent
from app.services.ppt_generator import generate_ieee_presentation
from app.services.pdf_report import generate_ieee_pdf
from app.services.search_service import search_academic_papers

# ==========================================================
# Create FastAPI Application
# ==========================================================
app = FastAPI(
    title="ResearchX API",
    version="2.0.0",
)

# ==========================================================
# CORS Configuration (Allows Frontend Port 8080 & 5173)
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Global Error Handler
# ==========================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"Internal server error: {str(exc)}",
            "data": None,
        },
    )

# ==========================================================
# Root & Health Check Routes
# ==========================================================
@app.get("/")
def root():
    return success_response(
        message="ResearchX Backend Running Successfully",
        data={"status": "OK", "version": "2.0.0"},
    )

@app.get("/health")
def health():
    return success_response(
        message="ResearchX Backend is Healthy",
        data={"status": "OK"},
    )

# ==========================================================
# Direct Multi-Agent Execution Endpoint
# ==========================================================
class AgentRequest(BaseModel):
    query: str
    paper_name: Optional[str] = None
    context: Optional[str] = None

@app.post("/api/run-agent")
def execute_agent(req: AgentRequest):
    return run_agent(query=req.query, paper_name=req.paper_name, context=req.context)

# ==========================================================
# IEEE PPT & PDF Download Endpoints
# ==========================================================
@app.post("/api/generate-ppt")
def create_ppt_endpoint(paper_title: str):
    summary_data = run_agent(query="summary", paper_name=paper_title)
    gaps_data = run_agent(query="gaps", paper_name=paper_title)

    summary_text = summary_data["results"]["summary"]["output"]
    gaps_text = gaps_data["results"]["gaps"]["output"]

    slides = [
        {"heading": "1. Executive Summary", "points": [summary_text[:300]]},
        {"heading": "2. Research Gaps & Limitations", "points": [gaps_text[:300]]},
        {"heading": "3. Future Directions & Next Steps", "points": ["Address dataset diversity and scalability", "Enhance architectural efficiency on edge devices"]}
    ]
    file_path = generate_ieee_presentation(paper_title, slides)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{paper_title[:15]}_presentation.pptx"
    )

@app.post("/api/generate-ieee-report")
def create_report_endpoint(paper_title: str):
    s = run_agent(query="summary", paper_name=paper_title)["results"]["summary"]["output"]
    g = run_agent(query="gaps", paper_name=paper_title)["results"]["gaps"]["output"]
    e = run_agent(query="experiments", paper_name=paper_title)["results"]["experiments"]["output"]

    file_path = generate_ieee_pdf(paper_title, s, g, e)
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"{paper_title[:15]}_IEEE_Report.pdf"
    )

# ==========================================================
# Include Existing Modular Routers
# ==========================================================
app.include_router(router)
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(analysis_router)
app.include_router(report_router)
app.include_router(ppt_router)
app.include_router(presentation_router)
app.include_router(dashboard_router)
app.include_router(paper_search_router, prefix="/api")