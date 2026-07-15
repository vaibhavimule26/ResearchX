import os

from dotenv import load_dotenv

# ==========================================================
# Load Environment Variables FIRST
# ==========================================================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True,
)

# ==========================================================
# FastAPI Imports
# ==========================================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ==========================================================
# Application Imports
# IMPORTANT: Keep these AFTER load_dotenv()
# ==========================================================
from app.utils.response import success_response
from app.api.routes import router
from app.upload.upload import router as upload_router
from app.search.search import router as search_router
from app.api.analysis import router as analysis_router
from app.api.report import router as report_router
from app.api.ppt import router as ppt_router

# ==========================================================
# Create FastAPI Application
# ==========================================================
app = FastAPI(
    title="ResearchX API",
    version="1.0.0",
)

# ==========================================================
# CORS Configuration
# ==========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Global Error Handler
# ==========================================================
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    print(
        f"Unhandled error: {type(exc).__name__}: {exc}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None,
        },
    )

# ==========================================================
# Root Route
# ==========================================================
@app.get("/")
def root():
    return success_response(
        message="ResearchX Backend Running Successfully",
        data={
            "status": "OK",
            "version": "1.0.0",
        },
    )

# ==========================================================
# Health Check
# ==========================================================
@app.get("/health")
def health():
    return success_response(
        message="ResearchX Backend is Healthy",
        data={
            "status": "OK",
        },
    )

# ==========================================================
# Authentication Routes
# ==========================================================
app.include_router(router)

# ==========================================================
# Upload Routes
# ==========================================================
app.include_router(upload_router)

# ==========================================================
# Search Routes
# ==========================================================
app.include_router(search_router)

# ==========================================================
# Structured Analysis Routes
# ==========================================================
app.include_router(analysis_router)

# ==========================================================
# IEEE Report Routes
# ==========================================================
app.include_router(report_router)

# ==========================================================
# PPT Generator Routes
# ==========================================================
app.include_router(ppt_router)