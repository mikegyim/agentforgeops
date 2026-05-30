"""Incident Triage Agent — correlates logs/metrics, suggests root cause + runbook."""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

from app.agents.base import Agent
from app.integrations.llm import get_llm
from app.integrations.prometheus import PrometheusMock
from app.rag.retriever import retrieve

ERROR_PATTERNS = [
    r"ERROR",
    r"FATAL",
    r"Exception",
    r"Traceback",
    r"timeout",
    r"connection refused",
    r"OOMKilled",
    r"CrashLoopBackOff",
]


class IncidentTriageAgent(Agent):
    name = "Incident Triage Agent"
    description = "Correlates logs and metrics, proposes root cause + runbook steps."

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logs: str = payload.get("logs", "")
        service: str = payload.get("service", "unknown")
        time_window: str = payload.get("time_window", "15m")

        errors = self._extract_errors(logs)
        signatures = Counter(errors).most_common(5)

        prom = PrometheusMock()
        metrics = await prom.snapshot(service=service, window=time_window)

        # Pull runbooks for the top signature.
        runbook_query = f"{service} {signatures[0][0] if signatures else 'incident'}"
        hits = await retrieve(runbook_query, top_k=4)
        runbook_ctx = "\n".join(f"- ({h.source}) {h.text[:300]}" for h in hits)

        llm = get_llm()
        analysis = await llm.complete(
            "You are an SRE on call. Correlate the signals below into a likely root cause "
            "and a 5-step remediation plan grounded in the linked runbooks.\n\n"
            f"# Service\n{service}\n\n"
            f"# Top error signatures\n{signatures}\n\n"
            f"# Metrics snapshot\n{metrics}\n\n"
            f"# Runbooks\n{runbook_ctx}\n"
        )

        return {
            "agent": self.name,
            "service": service,
            "signatures": signatures,
            "metrics": metrics,
            "runbooks": [h.source for h in hits],
            "analysis": analysis,
        }

    @staticmethod
    def _extract_errors(logs: str) -> List[str]:
        out: List[str] = []
        for line in logs.splitlines():
            for pat in ERROR_PATTERNS:
                if re.search(pat, line):
                    # Normalize numbers/ids out so we get signatures.
                    sig = re.sub(r"\d+", "N", line.strip())[:160]
                    out.append(sig)
                    break
        return out
