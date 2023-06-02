from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional, Union

import torch
from torch.utils.data import DataLoader
from torchmetrics import Metric

from ..config import EvaluatorType
from .downstream import ICLMetric

__all__ = ["Evaluator"]


@dataclass
class Evaluator:
    label: str
    type: EvaluatorType
    eval_loader: DataLoader
    eval_batches: Iterator[Dict[str, Any]]
    eval_metric: Union[Metric, Dict[str, Metric]]
    subset_num_batches: Optional[int] = None

    def reset_metrics(self) -> None:
        if isinstance(self.eval_metric, Metric):
            self.eval_metric.reset()
        else:
            for metric in self.eval_metric.values():
                metric.reset()

    def compute_metrics(self) -> Dict[str, float]:
        if self.type == EvaluatorType.downstream:
            assert isinstance(self.eval_metric, ICLMetric)
            return {
                f"eval/downstream/{self.label}_{self.eval_metric.metric_type}": self.eval_metric.compute().item(),
            }
        elif self.type == EvaluatorType.lm:
            # Metric(s) = cross entropy loss
            metrics: Dict[str, Metric]
            if isinstance(self.eval_metric, Metric):
                metrics = {self.label: self.eval_metric}
            else:
                metrics = self.eval_metric
            out = {}
            for label in sorted(metrics.keys()):
                metric = metrics[label]
                loss = metric.compute()
                out[f"eval/{label}/CrossEntropyLoss"] = loss.item()
                out[f"eval/{label}/Perplexity"] = torch.exp(loss).item()
            return out
        else:
            raise ValueError(f"Unexpected evaluator type '{self.type}'")

    def update_metrics(
        self,
        batch: Dict[str, Any],
        ce_loss: torch.Tensor,
        logits: torch.Tensor,
    ) -> None:
        if self.type == EvaluatorType.downstream:
            assert isinstance(self.eval_metric, ICLMetric)
            self.eval_metric.update(batch, logits)  # type: ignore
        elif self.type == EvaluatorType.lm:
            # Metric(s) = cross entropy loss
            for metadata, instance_loss in zip(batch["metadata"], ce_loss):
                if isinstance(self.eval_metric, dict):
                    metric = self.eval_metric[metadata["label"]]
                else:
                    metric = self.eval_metric
                metric.update(instance_loss)
        else:
            raise ValueError(f"Unexpected evaluator type '{self.type}'")
