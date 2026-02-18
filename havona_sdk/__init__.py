"""
Havona SDK — Python client for the Havona trade finance API.

Quick start::

    import os
    from havona_sdk import HavonaClient

    client = HavonaClient.from_credentials(
        base_url=os.environ["HAVONA_API_URL"],
        auth0_domain=os.environ["AUTH0_DOMAIN"],
        auth0_audience=os.environ["AUTH0_AUDIENCE"],
        auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
        username=os.environ["HAVONA_EMAIL"],
        password=os.environ["HAVONA_PASSWORD"],
    )

    trades = client.trades.list()
    status = client.blockchain.status()
"""

from .client import HavonaClient
from .exceptions import (
    AuthError,
    BlockchainError,
    GraphQLError,
    HavonaError,
    NotFoundError,
    ValidationError,
)
from .models import (
    Agent,
    AgentReputation,
    BlockchainPersistence,
    BlockchainStatus,
    ETRType,
    ExtractionResult,
    Trade,
)

__version__ = "0.1.0"

__all__ = [
    "HavonaClient",
    # Exceptions
    "HavonaError",
    "AuthError",
    "BlockchainError",
    "GraphQLError",
    "NotFoundError",
    "ValidationError",
    # Models
    "Trade",
    "BlockchainPersistence",
    "BlockchainStatus",
    "Agent",
    "AgentReputation",
    "ExtractionResult",
    "ETRType",
]
