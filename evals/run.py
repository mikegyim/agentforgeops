"""AgentForgeOps eval runner.

Usage (from `backend/`):
    PYTHONPATH=. python ../evals/run.py
    PYTHONPATH=. python ../evals/run.py --agent deploy-validator --threshold 0.8

Exits non-zero if overall pass-rate < threshold, so it works as a CI gate.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from app.agents.code_review import CodeReviewAgent
from app.agents.deploy_validator import DeployValidatorAgent
from app.agents.docs import DocsAgent
from app.agents.incident_triage import IncidentTriageAgent
from app.agents.test_generator import TestGeneratorAgent

AGENTS = {
    "code-review": CodeReviewAgent(),
    "test-gen": TestGeneratorAgent(),
    "deploy-validator": DeployValidatorAgent(),
    "incident-triage": IncidentTriageAgent(),
    "docs": DocsAgent(),
}


@dataclasses.dataclass
class CaseResult:
    agent: str
    case_id: str
    passed: int
    total: int
    failures: List[str]

    @property
    def score(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "case_id": self.case_id,
            "score": round(self.score, 3),
            "passed": self.passed,
            "total": self.total,
            "failures": self.failures,
        }


def _resolve(obj: Any, path: str) -> Any:
    """Walk a dot-path into nested dicts/lists. Returns None if missing."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if part.isdigit() and isinstance(cur, list):
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _check(assertion: Dict[str, Any], output: Dict[str, Any]) -> tuple[bool, str]:
    kind = assertion["kind"]
    field = assertion.get("field", "")
    expected = assertion.get("value")
    actual = _resolve(output, field) if field else output

    if kind == "contains":
        ok = isinstance(actual, str) and expected in actual
        return ok, f"expected '{expected}' in {field!r}"
    if kind == "not_contains":
        ok = isinstance(actual, str) and expected not in actual
        return ok, f"expected '{expected}' NOT in {field!r}"
    if kind == "regex":
        ok = isinstance(actual, str) and bool(re.search(expected, actual))
        return ok, f"expected regex /{expected}/ to match {field!r}"
    if kind == "equals":
        return actual == expected, f"expected {field!r}=={expected!r}, got {actual!r}"
    if kind == "min_len":
        try:
            ok = len(actual) >= int(expected)
        except TypeError:
            ok = False
        return ok, f"expected len({field!r}) >= {expected}, got {len(actual) if actual is not None else 0}"
    if kind == "in":
        ok = actual in (expected or [])
        return ok, f"expected {field!r} in {expected!r}, got {actual!r}"
    return False, f"unknown assertion kind: {kind}"


async def _run_case(agent_id: str, case: Dict[str, Any]) -> CaseResult:
    agent = AGENTS[agent_id]
    output = await agent.run(case.get("input", {}))
    passed = 0
    failures: List[str] = []
    for a in case.get("assertions", []):
        ok, msg = _check(a, output)
        if ok:
            passed += 1
        else:
            failures.append(msg)
    return CaseResult(
        agent=agent_id,
        case_id=case.get("id", "unknown"),
        passed=passed,
        total=len(case.get("assertions", [])),
        failures=failures,
    )


def _load_cases(root: Path, agent_filter: str | None) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for agent_dir in sorted(root.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent_id = agent_dir.name
        if agent_filter and agent_id != agent_filter:
            continue
        cases: List[Dict[str, Any]] = []
        for f in sorted(agent_dir.glob("*.json")):
            cases.append(json.loads(f.read_text()))
        if cases:
            out[agent_id] = cases
    return out


async def _main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--agent", default=None, help="Run only this agent.")
    p.add_argument("--threshold", type=float, default=0.7, help="Min pass-rate to succeed.")
    p.add_argument("--cases-dir", default=str(Path(__file__).parent / "cases"))
    p.add_argument("--report", default=str(Path(__file__).parent / "report.json"))
    args = p.parse_args()

    cases_by_agent = _load_cases(Path(args.cases_dir), args.agent)
    if not cases_by_agent:
        print(f"No cases found under {args.cases_dir}")
        return 1

    results: List[CaseResult] = []
    for agent_id, cases in cases_by_agent.items():
        for case in cases:
            r = await _run_case(agent_id, case)
            results.append(r)
            marker = "PASS" if r.score == 1.0 else ("PART" if r.score > 0 else "FAIL")
            print(f"[{marker}] {agent_id}/{r.case_id}  {r.passed}/{r.total}")
            for f in r.failures:
                print(f"        - {f}")

    total_assertions = sum(r.total for r in results)
    total_passed = sum(r.passed for r in results)
    pass_rate = (total_passed / total_assertions) if total_assertions else 0.0

    report = {
        "summary": {
            "cases": len(results),
            "assertions": total_assertions,
            "passed": total_passed,
            "pass_rate": round(pass_rate, 3),
            "threshold": args.threshold,
        },
        "results": [r.to_dict() for r in results],
    }
    Path(args.report).write_text(json.dumps(report, indent=2))
    print(f"\nOverall: {total_passed}/{total_assertions} = {pass_rate:.1%}")
    print(f"Report written to {args.report}")

    return 0 if pass_rate >= args.threshold else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
