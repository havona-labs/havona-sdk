# havona-sdk

Python client for the [Havona](https://github.com/havona-labs) trade finance API.

Havona is a dual-persistence trade contract platform — every write is committed to both a fast GraphQL layer (DGraph) and a confidential EVM blockchain (TEE-based audit trail).

---

## Install

```bash
pip install havona-sdk
```

Requires Python 3.9+ and `requests`.

---

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

# List trades
trades = client.trades.list(limit=10)
for t in trades:
    print(t.contract_no, t.status)

# Check blockchain connection
status = client.blockchain.status()
print(status.connected, status.chain_id)
```

---

## Authentication

Three modes are supported:

```python
# 1. Username + password (interactive users)
client = HavonaClient.from_credentials(base_url=..., ..., username=..., password=...)

# 2. M2M client credentials (service accounts)
client = HavonaClient.from_m2m(base_url=..., ..., auth0_client_id=..., auth0_client_secret=...)

# 3. Inject a pre-obtained bearer token
client = HavonaClient.from_token(base_url=..., token=my_jwt)
```

Tokens obtained via Auth0 are cached in memory and refreshed automatically when they expire.

---

## Resources

### Trades — `client.trades`

```python
# List
trades = client.trades.list(limit=100)

# Get by ID
trade = client.trades.get("trade-uuid")

# Create
trade = client.trades.create(
    contract_no="TC-2026-001",
    contract_type="SPOT",
    status="DRAFT",
    seller_id="member-uuid",
    buyer_id="member-uuid",
)

# Update
client.trades.update(trade.id, status="ACTIVE")

# Assign a private book classification
client.trades.assign_book(trade.id, "FX_BOOK_A")
```

### Documents — `client.documents`

ETR extraction and trade blotting use the same pattern: extract fields from a PDF, then save with `client.trades.create()`.

```python
# Extract a Commercial Invoice (does NOT save anything)
result = client.documents.extract("invoice.pdf", "COMMERCIAL_INVOICE")
print(result.fields, result.confidence)

# Convert extracted fields and save as a trade
trade = client.trades.create(**result.to_trade_fields(), status="DRAFT")

# Extract trade fields from an unstructured document (email / Excel)
result = client.documents.extract_trade("email_confirmation.pdf")

# List supported ETR document types
for t in client.documents.supported_types():
    print(t.id, t.name)
```

**ETR vs /dynamic — what goes where:**

| Step | API | What it does |
|------|-----|-------------|
| Extract | `POST /api/etr/extract` | AI extracts fields from PDF. **No persistence.** |
| Blot | `POST /api/blotting/extract-pdf` | AI extracts trade fields from unstructured doc. **No persistence.** |
| Save | `POST /dynamic` (via `client.trades.create`) | Persists to DGraph + blockchain. |

### Agents — `client.agents`

```python
agents = client.agents.list()
rep    = client.agents.get_reputation(agent_id=1)
print(rep.average_score, rep.total_feedback)
```

### Blockchain — `client.blockchain`

```python
status = client.blockchain.status()
# BlockchainStatus(connected=True, chain_id=23295, contract_address="0x...")

persistence = client.blockchain.get_persistence("trade-uuid")
# BlockchainPersistence(status="CONFIRMED", tx_hash="0x...", block_number=12345)
```

### Raw passthrough

```python
# GraphQL query
data = client.graphql("""
    query {
        queryTradeContract(first: 5) {
            id contractNo status
        }
    }
""")

# Direct /dynamic write (for types not covered by resources)
result = client.write("ETRDocument", {
    "documentType": "BILL_OF_LADING",
    "tradeContractId": trade_id,
})
```

---

## Error handling

```python
from havona_sdk import HavonaError, AuthError, NotFoundError, ValidationError

try:
    trade = client.trades.get("nonexistent-id")
except NotFoundError:
    print("Trade not found")
except AuthError:
    print("Check your credentials")
except ValidationError as e:
    print(f"Bad payload: {e}")
except HavonaError as e:
    print(f"API error {e.status_code}: {e}")
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```
HAVONA_API_URL=https://api.yourdomain.com
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://api.yourdomain.com
AUTH0_CLIENT_ID=your_client_id
HAVONA_EMAIL=trader@yourdomain.com
HAVONA_PASSWORD=...
```

---

## Examples

See `examples/` for runnable scripts:

| File | What it shows |
|------|--------------|
| `01_get_started.py` | Connect, list trades, check blockchain |
| `02_create_trade.py` | Full trade lifecycle: create → update → confirm |
| `03_extract_document.py` | ETR extraction and trade blotting |
| `04_agent_registry.py` | List agents, inspect reputation |

---

## License

MIT — see [LICENSE](LICENSE).
