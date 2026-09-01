"""AI evaluation metrics for observability and backend integration."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from ai_tutor.models import AIMetadata

logger = logging.getLogger("AIMetrics")


@dataclass
class AIMetricsRecord:
    operation: str
    latency_ms: float
    provider: Optional[str] = None
    model_used: Optional[str] = None
    parse_success: bool = True
    prompt_truncated: bool = False
    scores_adjusted: bool = False
    output_sanitized: bool = False
    warnings_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_metadata(self, *, ai_engine_version: str, prompt_version: str) -> AIMetadata:
        return AIMetadata(
            ai_engine_version=ai_engine_version,
            prompt_version=prompt_version,
            operation=self.operation,
            provider=self.provider,
            model_used=self.model_used,
            latency_ms=round(self.latency_ms, 2),
            parse_success=self.parse_success,
            prompt_truncated=self.prompt_truncated,
            scores_adjusted=self.scores_adjusted,
            output_sanitized=self.output_sanitized,
            warnings_count=self.warnings_count,
            completed_at=self.timestamp,
            extra=self.metadata or None,
        )


class AIMetricsCollector:
    def __init__(self) -> None:
        self._records: List[AIMetricsRecord] = []
        self._max_records = 500

    @contextmanager
    def track(self, operation: str) -> Iterator[AIMetricsRecord]:
        record = AIMetricsRecord(operation=operation, latency_ms=0.0)
        start = time.perf_counter()
        try:
            yield record
        finally:
            record.latency_ms = (time.perf_counter() - start) * 1000
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records :]
            logger.info(
                "AI metrics | op=%s provider=%s model=%s latency_ms=%.1f parse_ok=%s truncated=%s",
                record.operation,
                record.provider,
                record.model_used,
                record.latency_ms,
                record.parse_success,
                record.prompt_truncated,
            )

    def recent(self, limit: int = 50) -> List[AIMetricsRecord]:
        return self._records[-limit:]

    def summary(self) -> Dict[str, Any]:
        if not self._records:
            return {"total_calls": 0}
        total = len(self._records)
        failures = sum(1 for r in self._records if not r.parse_success)
        truncated = sum(1 for r in self._records if r.prompt_truncated)
        avg_latency = sum(r.latency_ms for r in self._records) / total
        by_operation: Dict[str, int] = {}
        for r in self._records:
            by_operation[r.operation] = by_operation.get(r.operation, 0) + 1
        return {
            "total_calls": total,
            "parse_failures": failures,
            "truncated_calls": truncated,
            "avg_latency_ms": round(avg_latency, 2),
            "by_operation": by_operation,
        }


metrics_collector = AIMetricsCollector()
