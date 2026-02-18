"""
Lightweight response models for the Havona SDK.

These are plain dataclasses — no Pydantic required. Fields use snake_case
and match what the API returns. Unknown fields are stored in `extra`.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Trade:
    """A TradeContract record."""

    id: str
    contract_no: str
    status: str
    contract_type: Optional[str] = None
    blockchain_status: Optional[str] = None
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trade":
        bp = data.get("blockchainPersistence") or {}
        return cls(
            id=data.get("id", ""),
            contract_no=data.get("contractNo", ""),
            status=data.get("status", ""),
            contract_type=data.get("contractType"),
            blockchain_status=bp.get("status") or data.get("blockchain_status"),
            tx_hash=bp.get("txHash") or data.get("tx_hash"),
            block_number=bp.get("blockNumber") or data.get("block_number"),
            extra={k: v for k, v in data.items() if k not in
                  ("id", "contractNo", "status", "contractType", "blockchainPersistence")},
        )


@dataclass
class BlockchainPersistence:
    """Blockchain persistence record for a trade or document."""

    record_id: str
    status: str  # PENDING | CONFIRMED | FAILED
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    attempt_count: int = 0
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockchainPersistence":
        return cls(
            record_id=data.get("recordId", ""),
            status=data.get("status", ""),
            tx_hash=data.get("txHash"),
            block_number=data.get("blockNumber"),
            attempt_count=data.get("attemptCount", 0),
            created_at=data.get("createdAt"),
        )


@dataclass
class BlockchainStatus:
    """Current blockchain connection status from the Havona server."""

    connected: bool
    chain_id: Optional[int] = None
    network: Optional[str] = None
    contract_address: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockchainStatus":
        return cls(
            connected=data.get("connected", False),
            chain_id=data.get("chain_id") or data.get("chainId"),
            network=data.get("network"),
            contract_address=data.get("contract_address") or data.get("contractAddress"),
            extra={k: v for k, v in data.items()
                   if k not in ("connected", "chain_id", "chainId", "network",
                                "contract_address", "contractAddress")},
        )


@dataclass
class Agent:
    """An ERC-8004 registered agent."""

    id: int
    name: str
    agent_type: str
    wallet: Optional[str] = None
    status: Optional[str] = None
    metadata_uri: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            agent_type=data.get("agentType") or data.get("type", ""),
            wallet=data.get("wallet") or data.get("agentWallet"),
            status=data.get("status"),
            metadata_uri=data.get("metadataUri") or data.get("tokenURI"),
            extra={k: v for k, v in data.items()
                   if k not in ("id", "name", "agentType", "type", "wallet",
                                "agentWallet", "status", "metadataUri", "tokenURI")},
        )


@dataclass
class AgentReputation:
    """Aggregated reputation score for an agent."""

    agent_id: int
    total_feedback: int
    average_score: Optional[float] = None
    breakdown: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, agent_id: int, data: Dict[str, Any]) -> "AgentReputation":
        return cls(
            agent_id=agent_id,
            total_feedback=data.get("totalFeedback") or data.get("total_feedback", 0),
            average_score=data.get("averageScore") or data.get("average_score"),
            breakdown=data.get("breakdown", []),
        )


@dataclass
class ExtractionResult:
    """Result of a document extraction (PDF, Excel, or structured input)."""

    document_type: str
    fields: Dict[str, Any]
    confidence: Optional[float] = None
    source: Optional[str] = None  # "pdf" | "excel" | "ai"
    uploaded_filename: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_trade_fields(self) -> Dict[str, Any]:
        """
        Convert extracted fields into a payload suitable for client.trades.create().

        Returns a dict of trade fields. The caller can add or override fields:

            result = client.documents.extract_pdf("invoice.pdf")
            trade = client.trades.create(**result.to_trade_fields(), status="DRAFT")
        """
        # Normalise common field names the extractor returns
        payload = {}
        field_map = {
            "contractNo": "contract_no",
            "contractType": "contract_type",
            "commodity": "commodity",
            "quantity": "quantity",
            "unit": "unit",
            "unitPrice": "unit_price",
            "currency": "currency",
            "totalValue": "total_value",
            "originCountry": "origin_country",
            "destinationCountry": "destination_country",
            "shipmentDate": "shipment_date",
            "paymentTerms": "payment_terms",
            "incoterms": "incoterms",
            "description": "description",
        }

        # First pass: use extracted field names as-is (camelCase from server)
        for server_key in field_map:
            if server_key in self.fields:
                payload[server_key] = self.fields[server_key]

        # Second pass: accept snake_case aliases
        for server_key, snake_key in field_map.items():
            if snake_key in self.fields and server_key not in payload:
                payload[server_key] = self.fields[snake_key]

        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionResult":
        # Server wraps result under "extractedData" or "fields"
        fields = (
            data.get("extractedData")
            or data.get("fields")
            or data.get("result")
            or {k: v for k, v in data.items()
                if k not in ("documentType", "document_type", "confidence",
                             "source", "uploadedFilename", "pdfMetadata")}
        )
        return cls(
            document_type=data.get("documentType") or data.get("document_type", "unknown"),
            fields=fields if isinstance(fields, dict) else {},
            confidence=data.get("confidence"),
            source=data.get("source"),
            uploaded_filename=data.get("uploadedFilename"),
            raw=data,
        )


@dataclass
class ETRType:
    """An ETR document type supported by the extraction service."""

    id: str
    name: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ETRType":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
        )
