"""
ETRs resource — Electronic Trade Record document types and extraction.

This is a focused wrapper around ``POST /api/etr/extract`` and
``GET /api/etr/types``.  For the full extraction pipeline including trade
blotting see :class:`~havona_sdk.resources.documents.DocumentsResource`.

The relationship between ETR extraction and persistence:

1. **Extract** — call ``client.etrs.extract(file, document_type)`` to get
   structured fields from a PDF.  Nothing is saved.

2. **Persist** — call ``client.write("ETRDocument", {...})`` or
   ``client.trades.create(**result.to_trade_fields())`` to save the data.
"""

from typing import List, Optional, TYPE_CHECKING

from ..models import ETRType, ExtractionResult

if TYPE_CHECKING:
    from ..client import HavonaClient


class ETRsResource:
    """
    ETR document type catalogue and AI extraction.

    Usage::

        # List supported document types
        for t in client.etrs.types():
            print(t.id, t.name)

        # Extract a Bill of Lading
        result = client.etrs.extract("bol.pdf", "BILL_OF_LADING")
        print(result.fields)

        # Save to the platform
        client.write("ETRDocument", {
            "documentType": result.document_type,
            "tradeContractId": trade_id,
            **result.to_trade_fields(),
        })
    """

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def types(self) -> List[ETRType]:
        """
        Return the list of ETR document types the platform supports.

        Returns:
            List of :class:`~havona_sdk.models.ETRType`
        """
        resp = self._client._request("GET", "/api/etr/types")
        raw = resp.json()
        if isinstance(raw, list):
            items = raw
        else:
            items = raw.get("types") or raw.get("documentTypes") or []
        return [ETRType.from_dict(item) for item in items]

    def extract(
        self,
        file_path: str,
        document_type: str,
        mode: str = "native",
    ) -> ExtractionResult:
        """
        Extract structured fields from an ETR document PDF.

        This is an alias for :meth:`~havona_sdk.resources.documents.DocumentsResource.extract`.
        Nothing is persisted — use ``client.write()`` to save the result.

        Args:
            file_path: Path to the PDF.
            document_type: One of ``COMMERCIAL_INVOICE``, ``BILL_OF_LADING``,
                ``CERTIFICATE_OF_ORIGIN``.
            mode: ``"native"`` (Gemini vision, default) or ``"text"``.

        Returns:
            :class:`~havona_sdk.models.ExtractionResult`
        """
        return self._client.documents.extract(file_path, document_type, mode)
