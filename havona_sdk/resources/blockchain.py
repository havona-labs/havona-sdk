"""
Blockchain resource — connection status and persistence records.

The Havona platform dual-persists every write: DGraph (fast query layer)
and a confidential EVM blockchain (TEE-based audit trail).

These endpoints let you inspect the blockchain layer directly without
needing to query the chain yourself.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from ..models import BlockchainPersistence, BlockchainStatus

if TYPE_CHECKING:
    from ..client import HavonaClient


class BlockchainResource:

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def status(self) -> BlockchainStatus:
        resp = self._client._request("GET", "/api/blockchain/status")
        return BlockchainStatus.from_dict(resp.json())

    def get_persistence(self, record_id: str) -> BlockchainPersistence:
        resp = self._client._request("GET", f"/api/blockchain/persistence/{record_id}")
        return BlockchainPersistence.from_dict(resp.json())

    def raw_status(self) -> Dict[str, Any]:
        """Return the raw blockchain status dict without model parsing."""
        resp = self._client._request("GET", "/api/blockchain/status")
        return resp.json()
