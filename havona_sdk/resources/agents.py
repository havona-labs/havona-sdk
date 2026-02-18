"""
Agents resource — ERC-8004 agent registry and reputation.

Agents are autonomous AI entities registered on-chain with verifiable
identity and a community reputation score.

Endpoints:
    GET  /api/agents              list agents
    GET  /api/agents/<id>         agent detail
    GET  /api/agents/<id>/reputation  reputation summary
    GET  /api/agents/status       service health
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..models import Agent, AgentReputation

if TYPE_CHECKING:
    from ..client import HavonaClient


class AgentsResource:
    """
    Interact with the on-chain agent registry.

    Usage::

        agents = client.agents.list()
        for agent in agents:
            print(agent.id, agent.name, agent.agent_type)

        reputation = client.agents.get_reputation(1)
        print(f"Average score: {reputation.average_score}")
    """

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def list(self) -> List[Agent]:
        """
        List all registered agents from the on-chain registry.

        Returns:
            List of :class:`~havona_sdk.models.Agent` objects.
            Returns an empty list if the blockchain connection is unavailable.
        """
        resp = self._client._request("GET", "/api/agents")
        data = resp.json()
        raw_agents = data.get("agents") or []
        return [Agent.from_dict(a) for a in raw_agents]

    def get(self, agent_id: int) -> Agent:
        """
        Fetch a single agent by its on-chain ID.

        Args:
            agent_id: Integer agent ID assigned during registration.

        Returns:
            :class:`~havona_sdk.models.Agent`

        Raises:
            NotFoundError: If agent does not exist.
        """
        resp = self._client._request("GET", f"/api/agents/{agent_id}")
        return Agent.from_dict(resp.json())

    def get_reputation(self, agent_id: int) -> AgentReputation:
        """
        Fetch aggregated reputation for an agent.

        Args:
            agent_id: Integer agent ID.

        Returns:
            :class:`~havona_sdk.models.AgentReputation`
        """
        resp = self._client._request("GET", f"/api/agents/{agent_id}/reputation")
        return AgentReputation.from_dict(agent_id, resp.json())

    def status(self) -> Dict[str, Any]:
        """
        Return the health status of the agent registry service.

        Returns:
            Dict with keys such as ``connected``, ``contractAddress``,
            ``totalAgents``.
        """
        resp = self._client._request("GET", "/api/agents/status")
        return resp.json()
