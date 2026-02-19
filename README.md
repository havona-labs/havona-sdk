# havona-sdk

Python client for the [Havona](https://github.com/havona-labs) trade finance API.

Havona dual-persists everything: writes land in DGraph (fast queries) and on a confidential EVM chain (TEE-backed audit trail).

## Install

```bash
pip install havona-sdk
```

Requires Python 3.9+ and `requests`.

## Quick start

```python
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

trades = client.trades.list(limit=10)
status = client.blockchain.status()
```

## Auth

```python
# Password grant (user)
client = HavonaClient.from_credentials(base_url=..., ..., username=..., password=...)

# Client credentials (M2M / service account)
client = HavonaClient.from_m2m(base_url=..., ..., auth0_client_id=..., auth0_client_secret=...)

# Pre-obtained token
client = HavonaClient.from_token(base_url=..., token=my_jwt)
```

Tokens are cached and refreshed automatically.

## Resources

### `client.trades`

```python
trades = client.trades.list(limit=100)
trade  = client.trades.get("trade-uuid")

trade = client.trades.create(
    contract_no="TC-2026-001",
    contract_type="SPOT",
    status="DRAFT",
    seller_id="member-uuid",
    buyer_id="member-uuid",
)

client.trades.update(trade.id, status="ACTIVE")
client.trades.assign_book(trade.id, "FX_BOOK_A")
```

### `client.documents`

Extract fields from a PDF, then save with `client.trades.create()`.
Extraction endpoints return data only — nothing is persisted until you call `create()`.

```python
# ETR document (Commercial Invoice, Bill of Lading, Certificate of Origin)
result = client.documents.extract("invoice.pdf", "COMMERCIAL_INVOICE")
trade  = client.trades.create(**result.to_trade_fields(), status="DRAFT")

# Unstructured document (email confirmation, Excel)
result = client.documents.extract_trade("email_confirmation.pdf")

# Supported document types
for t in client.documents.supported_types():
    print(t.id, t.name)
```

### `client.agents`

```python
agents = client.agents.list()
rep    = client.agents.get_reputation(agent_id=1)
print(rep.average_score, rep.total_feedback)
```

### `client.blockchain`

```python
status = client.blockchain.status()
# BlockchainStatus(connected=True, chain_id=23295, contract_address="0x...")

persistence = client.blockchain.get_persistence("trade-uuid")
# BlockchainPersistence(status="CONFIRMED", tx_hash="0x...", block_number=12345)
```

### Raw passthrough

```python
data = client.graphql("""
    query { queryTradeContract(first: 5) { id contractNo status } }
""")

result = client.write("ETRDocument", {
    "documentType": "BILL_OF_LADING",
    "tradeContractId": trade_id,
})
```

## Errors

```python
from havona_sdk import HavonaError, AuthError, NotFoundError, ValidationError

try:
    trade = client.trades.get("nonexistent-id")
except NotFoundError:
    ...
except AuthError:
    ...
except HavonaError as e:
    print(e.status_code, e)
```

## Configuration

Copy `.env.example` and fill in your values. See `examples/` for runnable scripts.

## License

MIT
