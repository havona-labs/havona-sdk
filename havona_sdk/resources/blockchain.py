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
    """
    Inspect blockchain connection status and per-record persistence state.

    Usage::

        status = client.blockchain.status()
        if status.connected:
            print(f"Chain ID: {status.chain_id}")
            print(f"Contract: {status.contract_address}")

        # Check whether a specific record has been confirmed on-chain
        persistence = client.blockchain.get_persistence("trade-uuid")
        print(persistence.status)   # PENDING | CONFIRMED | FAILED
        print(persistence.tx_hash)
    """

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def status(self) -> BlockchainStatus:
        """
        Return the current blockchain connection status.

        Returns:
            :class:`~havona_sdk.models.BlockchainStatus`

        Example::

            status = client.blockchain.status()
            print("Connected:", status.connected)
            print("Chain ID:", status.chain_id)
            print("Contract:", status.contract_address)
        """
        resp = self._client._request("GET", "/api/blockchain/status")
        return BlockchainStatus.from_dict(resp.json())

    def get_persistence(self, record_id: str) -> BlockchainPersistence:
        """
        Fetch the blockchain persistence record for a specific DGraph record.

        Args:
            record_id: The DGraph UUID of the trade or document.

        Returns:
            :class:`~havona_sdk.models.BlockchainPersistence`

        Raises:
            NotFoundError: If no persistence record exists for this ID.
        """
        resp = self._client._request("GET", f"/api/blockchain/persistence/{record_id}")
        return BlockchainPersistence.from_dict(resp.json())

    def raw_status(self) -> Dict[str, Any]:
        """Return the raw blockchain status dict without model parsing."""
        resp = self._client._request("GET", "/api/blockchain/status")
        return resp.json()
