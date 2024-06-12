from typing import Any, Dict, Optional


class NFMetrics:
    def __init__(self, metrics_file: str):
        self.metrics_file = metrics_file

    def log(self, data: Dict[str, Any], step: int):
        with open(self.metrics_file, "a") as f:
            wrapped_data = {
                "metrics": data,
                "step": step,
            }
            f.write(f"{wrapped_data}\n")
