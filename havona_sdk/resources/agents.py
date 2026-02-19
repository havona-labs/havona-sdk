"""Agents resource — ERC-8004 on-chain agent registry and reputation."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..models import Agent, AgentReputation

if TYPE_CHECKING:
    from ..client import HavonaClient


class AgentsResource:

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def list(self) -> List[Agent]:
        """Returns an empty list if the blockchain connection is unavailable."""
        resp = self._client._request("GET", "/api/agents")
        data = resp.json()
        raw_agents = data.get("agents") or []
        return [Agent.from_dict(a) for a in raw_agents]

    def get(self, agent_id: int) -> Agent:
        resp = self._client._request("GET", f"/api/agents/{agent_id}")
        return Agent.from_dict(resp.json())

    def get_reputation(self, agent_id: int) -> AgentReputation:
        resp = self._client._request("GET", f"/api/agents/{agent_id}/reputation")
        return AgentReputation.from_dict(agent_id, resp.json())

    def status(self) -> Dict[str, Any]:
        resp = self._client._request("GET", "/api/agents/status")
        return resp.json()
