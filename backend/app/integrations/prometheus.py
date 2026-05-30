"""Mocked Prometheus integration. Returns plausible metric snapshots."""
from __future__ import annotations

import random
from typing import Any, Dict


class PrometheusMock:
    async def snapshot(self, service: str, window: str = "15m") -> Dict[str, Any]:
        random.seed(hash((service, window)) & 0xFFFFFFFF)
        return {
            "service": service,
            "window": window,
            "p50_latency_ms": random.randint(20, 200),
            "p99_latency_ms": random.randint(400, 3000),
            "error_rate_pct": round(random.uniform(0.1, 18.0), 2),
            "cpu_usage_pct": round(random.uniform(20, 95), 1),
            "memory_usage_pct": round(random.uniform(40, 98), 1),
            "pod_restarts_15m": random.randint(0, 12),
        }
