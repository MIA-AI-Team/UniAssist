"""Backward-compatible shim — use `from ai_tutor.metrics import ...` in new code."""

from ai_tutor.metrics import AIMetricsCollector, AIMetricsRecord, metrics_collector

__all__ = ["AIMetricsCollector", "AIMetricsRecord", "metrics_collector"]
