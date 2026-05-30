"""Thin GitHub API client used by the PR review pipeline."""
from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.config import settings

API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token

    def _headers(self, accept: str = "application/vnd.github+json") -> Dict[str, str]:
        h = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def get_pr_diff(self, repo: str, pr: int) -> str:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{API}/repos/{repo}/pulls/{pr}",
                headers=self._headers("application/vnd.github.v3.diff"),
            )
            r.raise_for_status()
            return r.text

    async def get_pr_files(self, repo: str, pr: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{API}/repos/{repo}/pulls/{pr}/files", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def post_pr_comment(self, repo: str, pr: int, body: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{API}/repos/{repo}/issues/{pr}/comments",
                headers=self._headers(),
                json={"body": body},
            )
            r.raise_for_status()
            return r.json()
