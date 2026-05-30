"""Base agent contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Agent(ABC):
    name: str = "agent"
    description: str = ""

    @abstractmethod
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...
