"""Test Generation Agent — proposes unit tests for changed code."""
from __future__ import annotations

from typing import Any, Dict

from app.agents.base import Agent
from app.integrations.llm import get_llm

PROMPT = """You are a test engineer. For the code below, produce a set of
unit tests that cover the happy path, edge cases, and at least one failure mode.
Use the team's preferred framework if provided ({framework}), otherwise pytest.

# Code
```{lang}
{code}
```

Return:
## Test plan
## Test code
"""


class TestGeneratorAgent(Agent):
    name = "Test Generation Agent"
    description = "Generates unit tests for new or changed code."

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        code = payload.get("code", "")
        lang = payload.get("language", "python")
        framework = payload.get("framework", "pytest")

        llm = get_llm()
        out = await llm.complete(PROMPT.format(code=code[:8000], lang=lang, framework=framework))
        return {
            "agent": self.name,
            "language": lang,
            "framework": framework,
            "tests": out,
        }
