"""
Documents resource — extract structured data from trade documents.

Two extraction pathways exist:

1. **ETR document extraction** (``extract``) — ``POST /api/etr/extract``

   Extracts structured fields from Electronic Trade Record PDFs:
   Commercial Invoice, Bill of Lading, Certificate of Origin.
   Uses Gemini AI vision.  **Does not persist anything.**

2. **Trade blotting extraction** (``extract_trade``) — ``POST /api/blotting/extract-pdf``

   Extracts TradeContract fields from unstructured trade documents
   (email confirmations, PDFs, Excel files).  **Does not persist anything.**

After extraction, call ``client.trades.create(**result.to_trade_fields())``
to save the extracted data.
"""

import os
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ..models import ETRType, ExtractionResult

if TYPE_CHECKING:
    from ..client import HavonaClient


class DocumentsResource:
    """
    Extract structured data from trade documents.

    Usage::

        # Extract a Commercial Invoice PDF
        result = client.documents.extract("invoice.pdf", "COMMERCIAL_INVOICE")
        print(result.fields)  # extracted key-value pairs
        print(result.confidence)  # 0.0 – 1.0

        # Save the extracted data as a trade
        trade = client.trades.create(**result.to_trade_fields(), status="DRAFT")

        # List supported ETR document types
        types = client.documents.supported_types()
    """

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def extract(
        self,
        file_path: str,
        document_type: str,
        mode: str = "native",
    ) -> ExtractionResult:
        """
        Extract structured fields from an ETR document PDF.

        Sends the PDF to ``POST /api/etr/extract`` for Gemini AI processing.
        **This does not save anything** — call ``client.trades.create()`` with
        the result to persist.

        Args:
            file_path: Path to the PDF file.
            document_type: One of ``COMMERCIAL_INVOICE``, ``BILL_OF_LADING``,
                ``CERTIFICATE_OF_ORIGIN``.
            mode: Extraction mode — ``"native"`` (Gemini vision, default) or
                ``"text"`` (text extraction fallback).

        Returns:
            :class:`~havona_sdk.models.ExtractionResult`

        Example::

            result = client.documents.extract(
                "invoice.pdf",
                document_type="COMMERCIAL_INVOICE",
            )
            # Inspect extracted fields
            print(result.fields.get("invoiceNumber"))
            print(result.confidence)

            # Convert to a trade-creation payload
            trade = client.trades.create(**result.to_trade_fields())
        """
        path = Path(file_path)
        with open(path, "rb") as fh:
            files = {"file": (path.name, fh, "application/pdf")}
            data = {"document_type": document_type, "mode": mode}
            resp = self._client._request(
                "POST",
                "/api/etr/extract",
                files=files,
                data=data,
            )
        return ExtractionResult.from_dict(resp.json())

    def extract_trade(
        self,
        file_path: str,
    ) -> ExtractionResult:
        """
        Extract TradeContract fields from an unstructured trade document.

        Sends the file to ``POST /api/blotting/extract-pdf`` which uses the
        blotting agent to identify trade details from email confirmations,
        PDFs, and spreadsheets.

        **This does not save anything.**

        Args:
            file_path: Path to the document file (PDF, Excel, etc.).

        Returns:
            :class:`~havona_sdk.models.ExtractionResult`

        Example::

            result = client.documents.extract_trade("email_confirmation.pdf")
            trade = client.trades.create(**result.to_trade_fields(), status="DRAFT")
        """
        path = Path(file_path)
        with open(path, "rb") as fh:
            content_type = _guess_content_type(path)
            files = {"file": (path.name, fh, content_type)}
            resp = self._client._request(
                "POST",
                "/api/blotting/extract-pdf",
                files=files,
            )
        return ExtractionResult.from_dict(resp.json())

    def supported_types(self) -> List[ETRType]:
        """
        Return the list of ETR document types supported by the extraction service.

        Returns:
            List of :class:`~havona_sdk.models.ETRType` objects.
        """
        resp = self._client._request("GET", "/api/etr/types")
        raw = resp.json()
        # Server may return a list or a dict with a "types" key
        if isinstance(raw, list):
            items = raw
        else:
            items = raw.get("types") or raw.get("documentTypes") or []
        return [ETRType.from_dict(item) for item in items]


def _guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
    }.get(suffix, "application/octet-stream")
