import os
import csv
import time
import threading
import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionMetric:
    """Individual execution performance measurement."""
    run_id: int
    agent_name: str
    query: str
    paper_name: str
    query_latency_ms: float
    retrieval_time_ms: float
    agent_execution_time_ms: float
    total_response_time_ms: float
    throughput_req_per_sec: float
    throughput_tokens_per_sec: float
    status: str
    output_length_chars: int = 0
    output_length_tokens: int = 0
    error_message: Optional[str] = None
    timestamp: str = ""
    model_name: Optional[str] = None
    provider: Optional[str] = None
    accuracy_score: Optional[float] = None
    accuracy_metrics: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LivePerformanceRegistry:
    """
    Thread-safe in-memory performance registry for recording live request latencies,
    agent execution metrics, throughput, and error rates.
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._lock = threading.Lock()
        self._metrics: List[ExecutionMetric] = []

    def record_metric(self, metric: ExecutionMetric):
        with self._lock:
            self._metrics.append(metric)
            if len(self._metrics) > self.max_history:
                self._metrics.pop(0)

    def get_metrics(self, limit: Optional[int] = None) -> List[ExecutionMetric]:
        with self._lock:
            if limit:
                return list(self._metrics[-limit:])
            return list(self._metrics)

    def clear(self):
        with self._lock:
            self._metrics.clear()

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            total_reqs = len(self._metrics)
            if total_reqs == 0:
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "failure_rate_pct": 0.0,
                    "avg_query_latency_ms": 0.0,
                    "avg_retrieval_time_ms": 0.0,
                    "avg_agent_execution_time_ms": 0.0,
                    "avg_total_response_time_ms": 0.0,
                    "avg_throughput_req_per_sec": 0.0,
                    "recent_executions_count": 0,
                }

            success_count = sum(1 for m in self._metrics if m.status == "SUCCESS")
            failed_count = total_reqs - success_count
            fail_rate = (failed_count / total_reqs) * 100.0

            avg_q = sum(m.query_latency_ms for m in self._metrics) / total_reqs
            avg_r = sum(m.retrieval_time_ms for m in self._metrics) / total_reqs
            avg_a = sum(m.agent_execution_time_ms for m in self._metrics) / total_reqs
            avg_tot = sum(m.total_response_time_ms for m in self._metrics) / total_reqs
            avg_tp = sum(m.throughput_req_per_sec for m in self._metrics) / total_reqs

            return {
                "total_requests": total_reqs,
                "successful_requests": success_count,
                "failed_requests": failed_count,
                "failure_rate_pct": round(fail_rate, 2),
                "avg_query_latency_ms": round(avg_q, 2),
                "avg_retrieval_time_ms": round(avg_r, 2),
                "avg_agent_execution_time_ms": round(avg_a, 2),
                "avg_total_response_time_ms": round(avg_tot, 2),
                "avg_throughput_req_per_sec": round(avg_tp, 4),
                "recent_executions_count": total_reqs,
            }

    def export_to_csv(self, filepath: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "RUN_ID",
                "AGENT",
                "MODEL",
                "PROVIDER",
                "QUERY",
                "PAPER_NAME",
                "STATUS",
                "QUERY_LATENCY_MS",
                "RETRIEVAL_TIME_MS",
                "AGENT_EXEC_TIME_MS",
                "TOTAL_RESPONSE_TIME_MS",
                "THROUGHPUT_REQ_PER_SEC",
                "THROUGHPUT_TOKENS_PER_SEC",
                "ACCURACY_SCORE_PCT",
                "OUTPUT_CHARS",
                "OUTPUT_TOKENS",
                "ERROR_MESSAGE",
                "TIMESTAMP",
            ])
            with self._lock:
                for m in self._metrics:
                    writer.writerow([
                        m.run_id,
                        m.agent_name,
                        m.model_name or "",
                        m.provider or "",
                        m.query,
                        m.paper_name,
                        m.status,
                        m.query_latency_ms,
                        m.retrieval_time_ms,
                        m.agent_execution_time_ms,
                        m.total_response_time_ms,
                        m.throughput_req_per_sec,
                        m.throughput_tokens_per_sec,
                        m.accuracy_score if m.accuracy_score is not None else "",
                        m.output_length_chars,
                        m.output_length_tokens,
                        m.error_message or "",
                        m.timestamp,
                    ])
        return filepath


# Global registry instance
global_performance_registry = LivePerformanceRegistry()


class PerformanceTimer:
    """
    Lightweight performance tracker for measuring latency across
    PDF processing, retrieval, LLM generation, and agent execution stages.
    Fully backward-compatible with existing ResearchX codebase.
    """

    def __init__(self, operation_name: str = "ResearchX Request"):
        self.operation_name = operation_name
        self.start_time = time.time()
        self.stage_times: Dict[str, float] = {}
        self.stage_starts: Dict[str, float] = {}

    def start_stage(self, stage_name: str):
        self.stage_starts[stage_name] = time.time()

    def start(self, stage_name: str):
        self.start_stage(stage_name)

    def end_stage(self, stage_name: str) -> float:
        if stage_name in self.stage_starts:
            duration = time.time() - self.stage_starts.pop(stage_name)
            self.stage_times[stage_name] = (
                self.stage_times.get(stage_name, 0.0) + duration
            )
            return duration
        return 0.0

    def stop(self, stage_name: str) -> float:
        return self.end_stage(stage_name)

    def total_time(self) -> float:
        return time.time() - self.start_time

    def log_summary(self):
        total = self.total_time()
        print("\n" + "=" * 40)
        print("RESEARCHX PERFORMANCE")
        print("=" * 40)
        for stage, duration in self.stage_times.items():
            print(f"{stage:<22}: {duration:6.2f}s")
        print("-" * 40)
        print(f"{'TOTAL':<22}: {total:6.2f}s")
        print("=" * 40 + "\n")

    def print_summary(self):
        self.log_summary()
