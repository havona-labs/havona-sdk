"""
Trades resource — TradeContract CRUD.

Writes go through POST /dynamic (DGraph + blockchain).
Reads go through POST /graphql.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..models import Trade

if TYPE_CHECKING:
    from ..client import HavonaClient

_TRADE_FIELDS = """
    id
    contractNo
    status
    contractType
    sellerId
    buyerId
    blockchainPersistence {
        status
        txHash
        blockNumber
        attemptCount
    }
"""


class TradesResource:
    def __init__(self, client: "HavonaClient"):
        self._client = client

    def list(self, limit: int = 100, fields: Optional[str] = None) -> List[Trade]:
        gql_fields = fields or _TRADE_FIELDS
        data = self._client.graphql(
            f"query {{ queryTradeContract(first: {limit}) {{ {gql_fields} }} }}"
        )
        return [Trade.from_dict(r) for r in data.get("queryTradeContract") or []]

    def get(self, trade_id: str, fields: Optional[str] = None) -> Trade:
        from ..exceptions import NotFoundError

        gql_fields = fields or _TRADE_FIELDS
        data = self._client.graphql(
            f'query {{ getTradeContract(id: "{trade_id}") {{ {gql_fields} }} }}'
        )
        raw = data.get("getTradeContract")
        if raw is None:
            raise NotFoundError(f"TradeContract '{trade_id}' not found")
        return Trade.from_dict(raw)

    def create(self, **kwargs: Any) -> Trade:
        """
        Create a TradeContract. Accepts snake_case or camelCase field names.

            trade = client.trades.create(
                contract_no="TC-2026-001",
                status="DRAFT",
                seller_id="abc123",
                buyer_id="def456",
            )
        """
        result = self._client.write("TradeContract", _normalise_fields(kwargs))
        return Trade.from_dict(result)

    def update(self, trade_id: str, **kwargs: Any) -> Dict[str, Any]:
        payload = _normalise_fields(kwargs)
        payload["id"] = trade_id
        return self._client.write("TradeContract", payload)

    def assign_book(self, trade_id: str, book: str) -> Dict[str, Any]:
        """Book is party-specific — stripped from cross-namespace sync so each
        counterparty manages their own classification independently."""
        resp = self._client._request(
            "PATCH",
            f"/api/trades/{trade_id}/book",
            json={"book": book},
        )
        return resp.json()


def _normalise_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """snake_case → camelCase for common TradeContract fields."""
    _map = {
        "contract_no": "contractNo",
        "contract_type": "contractType",
        "seller_id": "sellerId",
        "buyer_id": "buyerId",
        "blockchain_status": "blockchainStatus",
        "payment_terms": "paymentTerms",
        "shipment_date": "shipmentDate",
        "origin_country": "originCountry",
        "destination_country": "destinationCountry",
        "unit_price": "unitPrice",
        "total_value": "totalValue",
    }
    return {_map.get(k, k): v for k, v in kwargs.items()}
