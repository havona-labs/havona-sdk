"""
HavonaClient — main entry point for the Havona SDK.

    client = HavonaClient.from_credentials(
        base_url=os.environ["HAVONA_API_URL"],
        auth0_domain=os.environ["AUTH0_DOMAIN"],
        auth0_audience=os.environ["AUTH0_AUDIENCE"],
        auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
        username=os.environ["HAVONA_EMAIL"],
        password=os.environ["HAVONA_PASSWORD"],
    )

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
    def __init__(self, base_url: str, token_provider, timeout: int = DEFAULT_TIMEOUT):
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout

        self.trades = TradesResource(self)
        self.documents = DocumentsResource(self)
        self.agents = AgentsResource(self)
        self.etrs = ETRsResource(self)
        self.blockchain = BlockchainResource(self)

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
        """Auth0 password grant. Tokens are cached and refreshed automatically."""
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
        """Auth0 client credentials (M2M). Note: these tokens carry no email claim
        and can't access user-scoped endpoints like /graphql."""
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
        """Inject a pre-obtained bearer token. No refresh logic."""
        return cls(base_url=base_url, token_provider=StaticToken(token), timeout=timeout)

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
            # Let requests set Content-Type with the multipart boundary
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

    def graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a GraphQL query against /graphql. Returns the ``data`` dict.

            data = client.graphql('''
                query { queryTradeContract(first: 10) { id contractNo status } }
            ''')
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = self._request("POST", "/graphql", json=payload)
        result = resp.json()

        if result.get("errors"):
            raise GraphQLError(result["errors"])

        return result.get("data", {})

    def write(self, type_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write via POST /dynamic. Omit ``id`` to create; include it to update.

            result = client.write("TradeContract", {"contractNo": "TC-001", "status": "DRAFT"})
            trade_id = result["id"]
        """
        data = {"type": type_name, **payload}
        resp = self._request("POST", "/dynamic", json=data)
        return resp.json()
