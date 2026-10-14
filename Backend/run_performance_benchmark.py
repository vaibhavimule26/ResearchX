#!/usr/bin/env python3
"""
ResearchX Performance & Accuracy Benchmark CLI Runner
Executes actual agent requests over 5-10 repeated runs, measuring:
- Query latency (ms): query normalization, intent routing, or RAG embedding creation
- Retrieval time (ms): ChromaDB vector retrieval or paper context loading
- Agent execution time (ms): LLM reasoning, diagramming, or PDF/PPTX artifact compilation
- Total response time (ms): End-to-end turnaround latency
- Request & token throughput (req/s & tokens/s)
- Successful/failed request counts & failure rate (%)
- Scholarly task-specific accuracy audit (%)

Evaluates ALL implemented ResearchX AI Agents:
1. summary            - Executive Summary Agent
2. gaps               - Research Gap Agent
3. datasets           - Dataset Recommendation Agent
4. experiments        - Experiment Recommendation Agent
5. literature_survey  - Literature Survey Agent
6. novelty            - Novelty Analysis Agent
7. comparison         - Paper Comparison Agent (multi-paper matrix)
8. report             - IEEE Report Agent (full workflow with architecture diagram & 2-column PDF)
9. presentation       - PPT Generator Agent (full workflow with slides & .pptx export)
10. chat              - AI Chat / Vector RAG Retrieval Agent

Calculates statistical averages and exports individual & combined CSVs for IEEE evaluation.
"""

import os
import sys
import argparse

# Ensure Backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.performance_monitor import PerformanceMonitor, BenchmarkSummary


def parse_args():
    parser = argparse.ArgumentParser(
        description="ResearchX Multi-Agent Performance & Empirical Accuracy Benchmark Suite"
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="summary",
        choices=[
            "summary",
            "gaps",
            "datasets",
            "experiments",
            "literature_survey",
            "novelty",
            "comparison",
            "report",
            "presentation",
            "chat",
        ],
        help="Target ResearchX agent to benchmark (default: summary)",
    )
    parser.add_argument(
        "--paper",
        type=str,
        default="research paper7.pdf",
        help="Target research paper in database/workspace (default: research paper7.pdf)",
    )
    parser.add_argument(
        "--papers",
        type=str,
        default=None,
        help="Comma-separated list of papers for multi-paper comparison (e.g. 'research paper7.pdf,research paper9.pdf')",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of repeated test runs (recommended: 5 to 10, default: 5)",
    )
    parser.add_argument(
        "--all-agents",
        action="store_true",
        help="Benchmark all 10 agents sequentially to construct complete IEEE comparative table",
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        default=True,
        help="Export results and statistical summary to CSV for IEEE evaluation (default: True)",
    )
    parser.add_argument(
        "--no-csv",
        dest="save_csv",
        action="store_false",
        help="Disable CSV export",
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default=None,
        help="Custom destination filepath for the CSV export",
    )
    parser.add_argument(
        "--accuracy",
        dest="evaluate_accuracy",
        action="store_true",
        default=True,
        help="Run agent-specific answer accuracy/rubric evaluation (default: True)",
    )
    parser.add_argument(
        "--no-accuracy",
        dest="evaluate_accuracy",
        action="store_false",
        help="Disable answer accuracy audit (measures pure performance only)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Enforce safe bounds for repeated runs
    runs_count = max(1, min(20, args.runs))

    monitor = PerformanceMonitor()

    multi_papers_list = None
    if args.papers:
        multi_papers_list = [p.strip() for p in args.papers.split(",") if p.strip()]

    if args.all_agents:
        print("\n" + "=" * 90)
        print(f" [ResearchX Benchmark] Starting Full 10-Agent Benchmark Suite ({runs_count} runs per agent)")
        print(f" Target Paper: {args.paper} | Accuracy Audit: {args.evaluate_accuracy} | Save CSV: {args.save_csv}")
        print("=" * 90)

        summaries = monitor.benchmark_all_agents(
            paper_name=args.paper,
            num_runs=runs_count,
            save_csv=args.save_csv,
            csv_path=args.csv_path,
            evaluate_accuracy=args.evaluate_accuracy,
            multi_papers=multi_papers_list,
        )
        print(f"\n[ResearchX Benchmark] Completed multi-agent benchmark across {len(summaries)} agents.")
        if args.save_csv:
            csv_dest = args.csv_path or "evaluation_data/ieee_all_agents_performance_evaluation.csv"
            print(f"[ResearchX Benchmark] Combined CSV Report: {os.path.abspath(csv_dest)}")
    else:
        canonical = monitor.normalize_agent_name(args.agent)
        print("\n" + "=" * 90)
        print(f" [ResearchX Benchmark] Starting Benchmark for Agent '{canonical}' ({runs_count} repeated runs)")
        print(f" Target Paper: {args.paper} | Accuracy Audit: {args.evaluate_accuracy} | Save CSV: {args.save_csv}")
        print("=" * 90)

        summary = monitor.run_benchmark(
            agent_name=canonical,
            paper_name=args.paper,
            num_runs=runs_count,
            save_csv=args.save_csv,
            csv_path=args.csv_path,
            print_report=True,
            evaluate_accuracy=args.evaluate_accuracy,
            multi_papers=multi_papers_list,
        )
        print(
            f"[ResearchX Benchmark] Completed {summary.total_runs} runs. "
            f"Success: {summary.successful_runs}/{summary.total_runs} (Failure Rate: {summary.failure_rate_pct}%)."
        )
        if summary.accuracy_score is not None:
            print(f"[ResearchX Benchmark] Answer Accuracy Score: {summary.accuracy_score}%")
        if summary.csv_path:
            print(f"[ResearchX Benchmark] CSV Output: {os.path.abspath(summary.csv_path)}")


if __name__ == "__main__":
    main()
