"""
Documents resource — extract structured fields from trade documents.

Neither extraction endpoint persists anything. Call client.trades.create() with
the result to save the data.
"""

import os
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ..models import ETRType, ExtractionResult

if TYPE_CHECKING:
    from ..client import HavonaClient


class DocumentsResource:

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def extract(
        self,
        file_path: str,
        document_type: str,
        mode: str = "native",
    ) -> ExtractionResult:
        """Extract fields from an ETR PDF (COMMERCIAL_INVOICE, BILL_OF_LADING, etc.). Nothing is saved."""
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

    def extract_trade(self, file_path: str) -> ExtractionResult:
        """Extract TradeContract fields from an unstructured document (email, PDF, Excel). Nothing is saved."""
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
