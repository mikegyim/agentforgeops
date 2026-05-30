"""Multi-agent orchestrator (LangGraph-inspired, no hard dep).

Each workflow is a list of nodes; nodes are `{agent: id, input_from: prev_key?}`.
The orchestrator threads state between nodes — the output of node N is available to
node N+1 under `state[node_id]`.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import Agent


class Orchestrator:
    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents

    async def run(self, workflow: List[Dict[str, Any]], initial: Dict[str, Any]) -> Dict[str, Any]:
        state: Dict[str, Any] = {"input": initial}
        trace: List[Dict[str, Any]] = []

        for node in workflow:
            agent_id = node["agent"]
            if agent_id not in self.agents:
                raise ValueError(f"unknown agent: {agent_id}")
            payload = self._resolve_payload(node, state)
            output = await self.agents[agent_id].run(payload)
            key = node.get("as", agent_id)
            state[key] = output
            trace.append({"node": key, "agent": agent_id, "summary_keys": list(output.keys())})

        return {"state": state, "trace": trace}

    @staticmethod
    def _resolve_payload(node: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if "input_from" in node:
            ref = node["input_from"]
            return state.get(ref, {})
        return node.get("input", state.get("input", {}))
