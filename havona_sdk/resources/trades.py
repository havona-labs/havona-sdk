"""
Trades resource — create, read, and update TradeContract records.

All writes go through POST /dynamic (dual-persisted to DGraph + blockchain).
All reads go through POST /graphql.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..models import Trade

if TYPE_CHECKING:
    from ..client import HavonaClient

# Default fields returned by list/get queries
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
    """
    Access TradeContract records.

    Usage::

        trades = client.trades.list()
        trade = client.trades.get("trade-uuid")

        new = client.trades.create(
            contract_no="TC-2026-001",
            status="DRAFT",
            seller_id="member-uuid",
        )

        client.trades.update(new.id, status="ACTIVE")
    """

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def list(
        self,
        limit: int = 100,
        fields: Optional[str] = None,
    ) -> List[Trade]:
        """
        List TradeContracts visible to the authenticated user.

        Args:
            limit: Maximum records to return.
            fields: Custom GraphQL field selection (defaults to standard fields).

        Returns:
            List of :class:`~havona_sdk.models.Trade` objects.
        """
        gql_fields = fields or _TRADE_FIELDS
        data = self._client.graphql(
            f"""
            query {{
                queryTradeContract(first: {limit}) {{
                    {gql_fields}
                }}
            }}
            """
        )
        raw = data.get("queryTradeContract") or []
        return [Trade.from_dict(r) for r in raw]

    def get(self, trade_id: str, fields: Optional[str] = None) -> Trade:
        """
        Fetch a single TradeContract by ID.

        Args:
            trade_id: The DGraph UUID of the trade.
            fields: Custom GraphQL field selection.

        Returns:
            :class:`~havona_sdk.models.Trade`

        Raises:
            NotFoundError: If no trade with that ID exists.
        """
        from ..exceptions import NotFoundError

        gql_fields = fields or _TRADE_FIELDS
        data = self._client.graphql(
            f"""
            query {{
                getTradeContract(id: "{trade_id}") {{
                    {gql_fields}
                }}
            }}
            """
        )
        raw = data.get("getTradeContract")
        if raw is None:
            raise NotFoundError(f"TradeContract '{trade_id}' not found")
        return Trade.from_dict(raw)

    def create(self, **kwargs: Any) -> Trade:
        """
        Create a new TradeContract.

        Keyword arguments map to the GraphQL schema fields (camelCase or
        snake_case both accepted via the server's field normalisation).

        Common fields:

        - ``contract_no`` / ``contractNo`` — unique contract identifier
        - ``status`` — e.g. ``"DRAFT"``, ``"ACTIVE"``
        - ``seller_id`` / ``sellerId`` — member UUID of the seller
        - ``buyer_id`` / ``buyerId`` — member UUID of the buyer
        - ``contract_type`` / ``contractType``

        Returns:
            :class:`~havona_sdk.models.Trade` with the server-assigned ``id``.

        Example::

            trade = client.trades.create(
                contract_no="TC-2026-001",
                status="DRAFT",
                seller_id="abc123",
                buyer_id="def456",
            )
            print(trade.id)
        """
        payload = _normalise_fields(kwargs)
        result = self._client.write("TradeContract", payload)
        return Trade.from_dict(result)

    def update(self, trade_id: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Update an existing TradeContract.

        Args:
            trade_id: The DGraph UUID of the trade.
            **kwargs: Fields to update (snake_case or camelCase).

        Returns:
            Raw server response dict.

        Example::

            client.trades.update(trade.id, status="ACTIVE")
        """
        payload = _normalise_fields(kwargs)
        payload["id"] = trade_id
        return self._client.write("TradeContract", payload)

    def assign_book(self, trade_id: str, book: str) -> Dict[str, Any]:
        """
        Assign a book classification to a trade (party-specific).

        Book is a private field — each party in a cross-company trade manages
        their own book independently. It is stripped during cross-namespace sync.

        Args:
            trade_id: The DGraph UUID of the trade.
            book: Book name or identifier (e.g. ``"FX_BOOK_A"``).

        Returns:
            Raw server response dict.
        """
        resp = self._client._request(
            "PATCH",
            f"/api/trades/{trade_id}/book",
            json={"book": book},
        )
        return resp.json()


def _normalise_fields(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert snake_case keys to camelCase so the API accepts them.

    Only performs simple one-level conversion for the most common fields.
    Nested dicts are passed through as-is.
    """
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
