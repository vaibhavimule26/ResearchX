import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from app.services.performance_monitor import PerformanceMonitor, BenchmarkSummary
from app.utils.metrics import global_performance_registry

router = APIRouter(prefix="/api/performance", tags=["Performance Monitoring"])


class BenchmarkRequest(BaseModel):
    agent_name: str = Field(
        default="summary",
        description="Agent to evaluate: summary, gaps, datasets, experiments, literature_survey, novelty, comparison, report, presentation, chat, or 'all'",
    )
    paper_name: Optional[str] = Field(
        default=None,
        description="Target research paper for context retrieval (default: research paper7.pdf)",
    )
    multi_papers: Optional[List[str]] = Field(
        default=None,
        description="List of papers for multi-paper comparison",
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional custom user query or prompt",
    )
    num_runs: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of repeated test runs (recommended 5–10)",
    )
    save_csv: bool = Field(
        default=True,
        description="Whether to export results to CSV for IEEE evaluation",
    )
    csv_path: Optional[str] = Field(
        default=None,
        description="Custom CSV file path",
    )
    evaluate_accuracy: bool = Field(
        default=True,
        description="Whether to execute task-specific answer accuracy/rubric audit",
    )


@router.post("/benchmark")
def run_agent_benchmark(req: BenchmarkRequest):
    """
    Executes actual ResearchX agent executions across 5-10 repeated runs,
    measuring query latency, retrieval time, agent execution time, total response time,
    throughput, successful/failed requests, failure rate, and answer accuracy.
    Calculates averages and exports results to CSV for IEEE evaluation.
    """
    try:
        monitor = PerformanceMonitor()
        clean_target = req.agent_name.strip().lower()

        if clean_target in ("all", "all_agents", "all-agents"):
            summaries = monitor.benchmark_all_agents(
                paper_name=req.paper_name,
                num_runs=req.num_runs,
                save_csv=req.save_csv,
                csv_path=req.csv_path,
                evaluate_accuracy=req.evaluate_accuracy,
                multi_papers=req.multi_papers,
            )
            return {
                "success": True,
                "message": f"Completed 10-agent empirical benchmark across {len(summaries)} agents",
                "data": {k: v.to_dict() for k, v in summaries.items()},
            }

        summary = monitor.run_benchmark(
            agent_name=req.agent_name,
            query=req.query,
            paper_name=req.paper_name,
            num_runs=req.num_runs,
            save_csv=req.save_csv,
            csv_path=req.csv_path,
            print_report=True,
            evaluate_accuracy=req.evaluate_accuracy,
            multi_papers=req.multi_papers,
        )

        return {
            "success": True,
            "message": f"Completed {summary.total_runs} empirical benchmark runs for '{summary.agent_name}'",
            "data": summary.to_dict(),
        }
    except Exception as e:
        print(f"[Performance Benchmark API Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark/all")
def run_all_agents_benchmark(
    paper_name: Optional[str] = None,
    num_runs: int = 5,
    save_csv: bool = True,
    evaluate_accuracy: bool = True,
):
    """
    Executes full multi-agent benchmark suite across all 10 ResearchX agents sequentially.
    """
    try:
        monitor = PerformanceMonitor()
        summaries = monitor.benchmark_all_agents(
            paper_name=paper_name,
            num_runs=num_runs,
            save_csv=save_csv,
            evaluate_accuracy=evaluate_accuracy,
        )
        return {
            "success": True,
            "message": f"Completed empirical benchmark across all {len(summaries)} ResearchX agents",
            "data": {k: v.to_dict() for k, v in summaries.items()},
        }
    except Exception as e:
        print(f"[All-Agent Benchmark API Error]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
def get_live_performance_metrics():
    """
    Returns live in-memory performance metrics, averages, throughput,
    and failure rate recorded during ResearchX server operations.
    """
    summary = global_performance_registry.get_summary()
    recent_runs = [
        m.to_dict() for m in global_performance_registry.get_metrics(limit=20)
    ]
    return {
        "success": True,
        "summary": summary,
        "recent_runs": recent_runs,
    }


@router.get("/download-csv")
def download_performance_csv(filepath: Optional[str] = Query(default=None)):
    """
    Downloads the generated IEEE performance evaluation CSV file.
    """
    target = filepath
    if not target:
        # Check standard evaluation data directory for most recent CSV
        eval_dir = "evaluation_data"
        if os.path.exists(eval_dir):
            csvs = [
                os.path.join(eval_dir, f)
                for f in os.listdir(eval_dir)
                if f.endswith(".csv")
            ]
            if csvs:
                csvs.sort(key=os.path.getmtime, reverse=True)
                target = csvs[0]

    if not target or not os.path.exists(target):
        raise HTTPException(
            status_code=404,
            detail="No performance benchmark CSV file found. Please run a benchmark first.",
        )

    return FileResponse(
        path=target,
        media_type="text/csv",
        filename=os.path.basename(target),
    )
