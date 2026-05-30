"""Endpoints that invoke individual agents and the orchestrator."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.code_review import CodeReviewAgent
from app.agents.deploy_validator import DeployValidatorAgent
from app.agents.docs import DocsAgent
from app.agents.incident_triage import IncidentTriageAgent
from app.agents.orchestrator import Orchestrator
from app.agents.test_generator import TestGeneratorAgent
from app.models.schemas import (
    CodeReviewRequest,
    DeployValidationRequest,
    DocsRequest,
    IncidentTriageRequest,
    OrchestrationRequest,
    TestGenerationRequest,
)

router = APIRouter()

_AGENTS = {
    "code-review": CodeReviewAgent(),
    "test-gen": TestGeneratorAgent(),
    "deploy-validator": DeployValidatorAgent(),
    "incident-triage": IncidentTriageAgent(),
    "docs": DocsAgent(),
}


@router.get("")
async def list_agents():
    return {
        "agents": [
            {"id": k, "name": v.name, "description": v.description}
            for k, v in _AGENTS.items()
        ]
    }


@router.post("/code-review")
async def code_review(req: CodeReviewRequest):
    return await _AGENTS["code-review"].run(req.model_dump())


@router.post("/test-gen")
async def test_gen(req: TestGenerationRequest):
    return await _AGENTS["test-gen"].run(req.model_dump())


@router.post("/deploy-validator")
async def deploy_validate(req: DeployValidationRequest):
    return await _AGENTS["deploy-validator"].run(req.model_dump())


@router.post("/incident-triage")
async def incident_triage(req: IncidentTriageRequest):
    return await _AGENTS["incident-triage"].run(req.model_dump())


@router.post("/docs")
async def docs(req: DocsRequest):
    return await _AGENTS["docs"].run(req.model_dump())


@router.post("/orchestrate")
async def orchestrate(req: OrchestrationRequest):
    """Run a multi-agent workflow (LangGraph-style)."""
    if not req.workflow:
        raise HTTPException(status_code=400, detail="workflow required")
    orch = Orchestrator(agents=_AGENTS)
    return await orch.run(req.workflow, req.input)
