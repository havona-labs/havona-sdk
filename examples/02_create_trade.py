"""
02 — Create and update a trade contract.

Shows the full lifecycle: DRAFT → ACTIVE, including a raw /dynamic write
for fields not exposed through the trades resource.

Prerequisites:
    pip install havona-sdk
    cp .env.example .env   # fill in your credentials
"""

import os
from dotenv import load_dotenv

load_dotenv()

from havona_sdk import HavonaClient, HavonaError, ValidationError

client = HavonaClient.from_credentials(
    base_url=os.environ["HAVONA_API_URL"],
    auth0_domain=os.environ["AUTH0_DOMAIN"],
    auth0_audience=os.environ["AUTH0_AUDIENCE"],
    auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
    username=os.environ["HAVONA_EMAIL"],
    password=os.environ["HAVONA_PASSWORD"],
)

# --- 1. Create a draft trade -----------------------------------------

print("Creating trade TC-2026-DEMO-001 ...")
try:
    trade = client.trades.create(
        contract_no="TC-2026-DEMO-001",
        contract_type="SPOT",
        status="DRAFT",
        # seller_id and buyer_id are member UUIDs from your platform
        # seller_id="your-seller-member-uuid",
        # buyer_id="your-buyer-member-uuid",
    )
    print(f"  Created: id={trade.id}  status={trade.status}")
except ValidationError as e:
    print(f"  Validation error: {e}")
    raise SystemExit(1)
except HavonaError as e:
    print(f"  Error: {e}")
    raise SystemExit(1)

# --- 2. Add commodity details via raw write --------------------------

print("Adding commodity details...")
result = client.write("TradeContract", {
    "id": trade.id,
    "commodity": "Crude Oil",
    "quantity": "50000",
    "unit": "BBL",
    "unitPrice": "82.50",
    "currency": "USD",
    "originCountry": "US",
    "destinationCountry": "DE",
})
print(f"  Updated: {result.get('id')}")

# --- 3. Activate the trade -------------------------------------------

print("Activating trade...")
client.trades.update(trade.id, status="ACTIVE")
print("  Status → ACTIVE")

# --- 4. Verify by reading back ----------------------------------------

refreshed = client.trades.get(trade.id)
print(f"\nFinal state:")
print(f"  id              = {refreshed.id}")
print(f"  contractNo      = {refreshed.contract_no}")
print(f"  status          = {refreshed.status}")
print(f"  blockchainStatus = {refreshed.blockchain_status or 'pending'}")
print(f"  txHash          = {refreshed.tx_hash or 'not yet confirmed'}")
