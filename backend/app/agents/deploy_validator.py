"""Deployment Validation Agent — analyzes K8s/Terraform manifests for risk."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from app.agents.base import Agent
from app.integrations.llm import get_llm


class DeployValidatorAgent(Agent):
    name = "Deployment Validation Agent"
    description = "Analyzes Kubernetes and Terraform changes for risk and policy violations."

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        manifests = payload.get("manifests", [])  # list of {path, content}
        findings: List[Dict[str, Any]] = []

        for m in manifests:
            path = m.get("path", "")
            content = m.get("content", "")
            findings.extend(self._static_checks(path, content))

        llm = get_llm()
        narrative = await llm.complete(
            "Summarize the deployment risks below for a release-readiness review.\n"
            f"Findings: {findings}\n"
        )
        risk = self._aggregate_risk(findings)
        return {
            "agent": self.name,
            "risk": risk,
            "findings": findings,
            "narrative": narrative,
        }

    @staticmethod
    def _static_checks(path: str, content: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        lower = content.lower()
        if path.endswith((".yaml", ".yml")) and "kind:" in lower:
            if "privileged: true" in lower:
                out.append({"path": path, "severity": "high", "msg": "privileged container"})
            if "runasuser: 0" in lower:
                out.append({"path": path, "severity": "high", "msg": "container runs as root"})
            if "resources:" not in lower:
                out.append({"path": path, "severity": "medium", "msg": "missing resource limits"})
            if re.search(r"image:\s*\S+:latest", content):
                out.append({"path": path, "severity": "medium", "msg": "uses :latest tag"})
            if "livenessprobe" not in lower:
                out.append({"path": path, "severity": "low", "msg": "no liveness probe"})
        if path.endswith(".tf"):
            if "public = true" in lower or '"0.0.0.0/0"' in content:
                out.append({"path": path, "severity": "high", "msg": "publicly exposed resource"})
            if "encrypted = false" in lower:
                out.append({"path": path, "severity": "high", "msg": "encryption disabled"})
        return out

    @staticmethod
    def _aggregate_risk(findings: List[Dict[str, Any]]) -> str:
        sev = {f["severity"] for f in findings}
        if "high" in sev:
            return "high"
        if "medium" in sev:
            return "medium"
        return "low"
