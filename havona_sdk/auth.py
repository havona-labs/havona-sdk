"""Auth0 token management — password grant, client credentials, and static token."""

import time
from typing import Optional

import requests

from .exceptions import AuthError


class _TokenCache:
    """In-memory cache for a single access token."""

    def __init__(self, access_token: str, expires_in: int = 86400):
        self.access_token = access_token
        # Subtract 60 s so we refresh slightly before actual expiry
        self._expires_at = time.monotonic() + expires_in - 60  # refresh slightly early

    def is_valid(self) -> bool:
        return time.monotonic() < self._expires_at


class Auth0:

    def __init__(
        self,
        domain: str,
        audience: str,
        client_id: str,
        *,
        client_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self._domain = domain.rstrip("/")
        self._audience = audience
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._cache: Optional[_TokenCache] = None

    @classmethod
    def from_password(cls, domain, audience, client_id, username, password) -> "Auth0":
        return cls(
            domain=domain,
            audience=audience,
            client_id=client_id,
            username=username,
            password=password,
        )

    @classmethod
    def from_client_credentials(cls, domain, audience, client_id, client_secret) -> "Auth0":
        return cls(
            domain=domain,
            audience=audience,
            client_id=client_id,
            client_secret=client_secret,
        )

    def get_token(self, force_refresh: bool = False) -> str:
        if not force_refresh and self._cache and self._cache.is_valid():
            return self._cache.access_token

        data = self._fetch_token()
        self._cache = _TokenCache(
            access_token=data["access_token"],
            expires_in=data.get("expires_in", 86400),
        )
        return self._cache.access_token

    def _fetch_token(self) -> dict:
        url = f"https://{self._domain}/oauth/token"

        if self._username and self._password:
            payload = {
                "grant_type": "password",
                "client_id": self._client_id,
                "audience": self._audience,
                "username": self._username,
                "password": self._password,
                "scope": "openid profile email",
            }
        elif self._client_secret:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "audience": self._audience,
            }
        else:
            raise AuthError(
                "No credentials configured. "
                "Use Auth0.from_password() or Auth0.from_client_credentials()."
            )

        try:
            resp = requests.post(url, json=payload, timeout=10)
        except requests.exceptions.RequestException as exc:
            raise AuthError(f"Auth0 request failed: {exc}") from exc

        if not resp.ok:
            raise AuthError(
                "Auth0 token request failed",
                status_code=resp.status_code,
                response_body=resp.text[:300],
            )

        token_data = resp.json()
        if "access_token" not in token_data:
            raise AuthError(f"Auth0 response missing access_token: {token_data}")

        return token_data


class StaticToken:
    """Pre-obtained bearer token with no refresh logic."""

    def __init__(self, token: str):
        self._token = token

    def get_token(self, force_refresh: bool = False) -> str:
        return self._token
