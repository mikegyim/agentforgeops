"""Smoke tests for agents — run with `pytest -q`."""
import asyncio

from app.agents.code_review import CodeReviewAgent
from app.agents.deploy_validator import DeployValidatorAgent
from app.agents.incident_triage import IncidentTriageAgent


def test_deploy_validator_flags_latest_tag():
    agent = DeployValidatorAgent()
    out = asyncio.run(
        agent.run(
            {
                "manifests": [
                    {
                        "path": "deployment.yaml",
                        "content": (
                            "apiVersion: apps/v1\nkind: Deployment\n"
                            "spec:\n  template:\n    spec:\n      containers:\n"
                            "      - name: web\n        image: nginx:latest\n"
                        ),
                    }
                ]
            }
        )
    )
    assert any("latest" in f["msg"] for f in out["findings"])
    assert out["risk"] in {"low", "medium", "high"}


def test_deploy_validator_flags_public_terraform():
    agent = DeployValidatorAgent()
    out = asyncio.run(
        agent.run(
            {
                "manifests": [
                    {
                        "path": "main.tf",
                        "content": 'resource "aws_s3_bucket" "x" { acl = "public-read"\n  cidr = "0.0.0.0/0"\n}',
                    }
                ]
            }
        )
    )
    assert out["risk"] == "high"


def test_incident_triage_extracts_signatures():
    agent = IncidentTriageAgent()
    logs = "\n".join(
        [
            "INFO starting up",
            "ERROR connection refused to db-host-12 after 5s",
            "ERROR connection refused to db-host-13 after 7s",
            "WARN slow query",
        ]
    )
    out = asyncio.run(agent.run({"logs": logs, "service": "checkout"}))
    assert out["service"] == "checkout"
    assert out["signatures"]


def test_code_review_runs_with_mock_llm():
    agent = CodeReviewAgent()
    out = asyncio.run(
        agent.run(
            {
                "diff": "diff --git a/x.py b/x.py\n+def add(a,b): return a+b\n",
                "files": [{"filename": "x.py"}],
            }
        )
    )
    assert "agent" in out
    assert "summary" in out
