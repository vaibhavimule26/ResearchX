import time
from typing import Dict, Optional


class PerformanceTimer:
    """
    Lightweight performance tracker for measuring latency across
    PDF processing, retrieval, LLM generation, and agent execution stages.
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
