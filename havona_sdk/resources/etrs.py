"""ETRs resource — document type catalogue and AI field extraction."""

from typing import List, Optional, TYPE_CHECKING

from ..models import ETRType, ExtractionResult

if TYPE_CHECKING:
    from ..client import HavonaClient


class ETRsResource:

    def __init__(self, client: "HavonaClient"):
        self._client = client

    def types(self) -> List[ETRType]:
        resp = self._client._request("GET", "/api/etr/types")
        raw = resp.json()
        if isinstance(raw, list):
            items = raw
        else:
            items = raw.get("types") or raw.get("documentTypes") or []
        return [ETRType.from_dict(item) for item in items]

    def extract(self, file_path: str, document_type: str, mode: str = "native") -> ExtractionResult:
        """Alias for client.documents.extract(). Nothing is persisted."""
        return self._client.documents.extract(file_path, document_type, mode)
