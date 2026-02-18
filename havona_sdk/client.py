"""
HavonaClient — the main entry point for the Havona SDK.

Usage:

    import os
    from havona_sdk import HavonaClient

    # Interactive user (Auth0 password grant)
    client = HavonaClient.from_credentials(
        base_url="https://api.yourdomain.com",
        auth0_domain=os.environ["AUTH0_DOMAIN"],
        auth0_audience=os.environ["AUTH0_AUDIENCE"],
        auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
        username=os.environ["HAVONA_EMAIL"],
        password=os.environ["HAVONA_PASSWORD"],
    )

    # Service account (M2M client credentials)
    client = HavonaClient.from_m2m(
        base_url="https://api.yourdomain.com",
        auth0_domain=os.environ["AUTH0_DOMAIN"],
        auth0_audience=os.environ["AUTH0_AUDIENCE"],
        auth0_client_id=os.environ["AUTH0_M2M_CLIENT_ID"],
        auth0_client_secret=os.environ["AUTH0_M2M_CLIENT_SECRET"],
    )

    # Inject a pre-obtained token
    client = HavonaClient.from_token(
        base_url="https://api.yourdomain.com",
        token=os.environ["HAVONA_TOKEN"],
    )

    # Use the typed resource APIs
    trade = client.trades.create(contract_no="TC-2026-001", status="DRAFT")
    status = client.blockchain.status()
"""

from typing import Any, Dict, Optional

import requests

from .auth import Auth0, StaticToken
from .exceptions import (
    AuthError,
    GraphQLError,
    HavonaError,
    NotFoundError,
    ValidationError,
)
from .resources.agents import AgentsResource
from .resources.blockchain import BlockchainResource
from .resources.documents import DocumentsResource
from .resources.etrs import ETRsResource
from .resources.trades import TradesResource

DEFAULT_TIMEOUT = 30


class HavonaClient:
    """
    Main client for the Havona API.

    All network calls go through this client. Sub-resources (.trades, .documents, etc.)
    delegate back here for authentication and HTTP transport.
    """

    def __init__(
        self,
        base_url: str,
        token_provider,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout

        # Typed resource sub-clients
        self.trades = TradesResource(self)
        self.documents = DocumentsResource(self)
        self.agents = AgentsResource(self)
        self.etrs = ETRsResource(self)
        self.blockchain = BlockchainResource(self)

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_credentials(
        cls,
        base_url: str,
        auth0_domain: str,
        auth0_audience: str,
        auth0_client_id: str,
        username: str,
        password: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> "HavonaClient":
        """
        Create a client authenticated via Auth0 username/password grant.

        Suitable for scripts and tools acting on behalf of a real user.
        Tokens are fetched lazily and cached until expiry.
        """
        auth = Auth0.from_password(
            domain=auth0_domain,
            audience=auth0_audience,
            client_id=auth0_client_id,
            username=username,
            password=password,
        )
        return cls(base_url=base_url, token_provider=auth, timeout=timeout)

    @classmethod
    def from_m2m(
        cls,
        base_url: str,
        auth0_domain: str,
        auth0_audience: str,
        auth0_client_id: str,
        auth0_client_secret: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> "HavonaClient":
        """
        Create a client authenticated via Auth0 M2M client credentials.

        Suitable for automated services that act at the platform level rather
        than on behalf of a specific user. Note: M2M tokens carry no email claim
        so they cannot access user-scoped endpoints like /graphql.
        """
        auth = Auth0.from_client_credentials(
            domain=auth0_domain,
            audience=auth0_audience,
            client_id=auth0_client_id,
            client_secret=auth0_client_secret,
        )
        return cls(base_url=base_url, token_provider=auth, timeout=timeout)

    @classmethod
    def from_token(
        cls,
        base_url: str,
        token: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> "HavonaClient":
        """
        Create a client with a pre-obtained bearer token.

        The token is used as-is with no refresh logic. Useful when your
        application already manages token lifecycle externally.
        """
        return cls(base_url=base_url, token_provider=StaticToken(token), timeout=timeout)

    # ------------------------------------------------------------------
    # Low-level HTTP helpers (used by resource classes)
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        token = self._token_provider.get_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files=None,
        data=None,
    ) -> requests.Response:
        url = f"{self._base_url}{path}"
        headers = self._headers()

        if files is not None:
            # Multipart upload: let requests set Content-Type with boundary
            headers.pop("Content-Type", None)

        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            params=params,
            files=files,
            data=data,
            timeout=self._timeout,
        )
        return self._raise_for_status(resp)

    def _raise_for_status(self, resp: requests.Response) -> requests.Response:
        """Convert HTTP error codes to typed SDK exceptions."""
        if resp.ok:
            return resp

        body = resp.text[:500]
        code = resp.status_code

        if code in (401, 403):
            msg = "Authentication failed" if code == 401 else "Forbidden — insufficient permissions"
            raise AuthError(msg, code, body)
        if code == 404:
            raise NotFoundError("Resource not found", code, body)
        if code in (400, 422):
            raise ValidationError("Validation error", code, body)

        raise HavonaError("Request failed", code, body)

    # ------------------------------------------------------------------
    # Raw passthrough APIs
    # ------------------------------------------------------------------

    def graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a raw GraphQL query against /graphql.

        Returns the ``data`` portion of the response. Raises GraphQLError
        if the response contains any GraphQL-level errors.

        Example::

            data = client.graphql('''
                query {
                    queryTradeContract(first: 10) {
                        id contractNo status
                    }
                }
            ''')
            trades = data.get("queryTradeContract", [])
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = self._request("POST", "/graphql", json=payload)
        result = resp.json()

        if result.get("errors"):
            raise GraphQLError(result["errors"])

        return result.get("data", {})

    def write(
        self,
        type_name: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Write a record via POST /dynamic.

        - Without ``id`` in payload: **creates** a new record (server assigns ID).
        - With ``id`` in payload: **updates** the existing record.

        Returns the server response dict, which includes ``id`` on creation.

        Example::

            result = client.write("TradeContract", {
                "contractNo": "TC-2026-001",
                "status": "DRAFT",
                "sellerId": "member-uuid",
            })
            trade_id = result["id"]
        """
        data = {"type": type_name, **payload}
        resp = self._request("POST", "/dynamic", json=data)
        return resp.json()
