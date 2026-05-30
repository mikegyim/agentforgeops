"""GitHub webhook receiver for AI PR review."""
from __future__ import annotations

import hashlib
import hmac
import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.agents.code_review import CodeReviewAgent
from app.config import settings
from app.integrations.github import GitHubClient

router = APIRouter()


def _verify_signature(secret: str, body: bytes, signature: str | None) -> bool:
    if not secret:
        return True  # dev mode
    if not signature or not signature.startswith("sha256="):
        return False
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()
    if not _verify_signature(settings.github_webhook_secret, body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="bad signature")

    payload = json.loads(body or b"{}")
    if x_github_event != "pull_request":
        return {"ignored": x_github_event}

    action = payload.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        return {"ignored_action": action}

    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]

    gh = GitHubClient()
    diff = await gh.get_pr_diff(repo, pr_number)
    files = await gh.get_pr_files(repo, pr_number)

    agent = CodeReviewAgent()
    review = await agent.run({"diff": diff, "files": files, "repo": repo, "pr": pr_number})

    await gh.post_pr_comment(repo, pr_number, review["summary"])
    return {"reviewed": True, "pr": pr_number, "repo": repo}
