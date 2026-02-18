"""
01 — Get started: connect and inspect your account.

Demonstrates the three ways to authenticate, then reads trades and
checks blockchain connectivity.

Prerequisites:
    pip install havona-sdk
    cp .env.example .env   # fill in your credentials
"""

import os
from dotenv import load_dotenv

load_dotenv()

from havona_sdk import HavonaClient, HavonaError

# ------------------------------------------------------------------
# Option A: username + password (interactive user)
# ------------------------------------------------------------------
client = HavonaClient.from_credentials(
    base_url=os.environ["HAVONA_API_URL"],
    auth0_domain=os.environ["AUTH0_DOMAIN"],
    auth0_audience=os.environ["AUTH0_AUDIENCE"],
    auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
    username=os.environ["HAVONA_EMAIL"],
    password=os.environ["HAVONA_PASSWORD"],
)

# ------------------------------------------------------------------
# Option B: M2M service account (uncomment to use)
# ------------------------------------------------------------------
# client = HavonaClient.from_m2m(
#     base_url=os.environ["HAVONA_API_URL"],
#     auth0_domain=os.environ["AUTH0_DOMAIN"],
#     auth0_audience=os.environ["AUTH0_AUDIENCE"],
#     auth0_client_id=os.environ["AUTH0_M2M_CLIENT_ID"],
#     auth0_client_secret=os.environ["AUTH0_M2M_CLIENT_SECRET"],
# )

# ------------------------------------------------------------------
# Option C: inject a pre-obtained token (uncomment to use)
# ------------------------------------------------------------------
# client = HavonaClient.from_token(
#     base_url=os.environ["HAVONA_API_URL"],
#     token=os.environ["HAVONA_TOKEN"],
# )

# --- 1. Blockchain connection -----------------------------------------

print("Checking blockchain status...")
try:
    status = client.blockchain.status()
    if status.connected:
        print(f"  Connected  chain={status.chain_id}  contract={status.contract_address}")
    else:
        print("  Blockchain not connected (platform may be running without a chain)")
except HavonaError as e:
    print(f"  Error: {e}")

# --- 2. List recent trades -------------------------------------------

print("\nFetching trades (first 10)...")
try:
    trades = client.trades.list(limit=10)
    if trades:
        for t in trades:
            print(f"  {t.contract_no:20s}  {t.status:10s}  blockchain={t.blockchain_status or 'n/a'}")
    else:
        print("  No trades found.")
except HavonaError as e:
    print(f"  Error: {e}")

# --- 3. Raw GraphQL passthrough --------------------------------------

print("\nRaw GraphQL query...")
try:
    data = client.graphql("""
        query {
            queryTradeContract(first: 3) {
                id
                contractNo
                status
            }
        }
    """)
    for t in data.get("queryTradeContract", []):
        print(f"  id={t['id'][:8]}  contractNo={t.get('contractNo')}")
except HavonaError as e:
    print(f"  Error: {e}")
