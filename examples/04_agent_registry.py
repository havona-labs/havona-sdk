"""
04 — Agent registry: list agents and inspect reputation.

The Havona platform supports ERC-8004 autonomous AI agents with
verifiable on-chain identity and community reputation scores.

This example lists all registered agents, fetches details on each,
and prints their aggregated reputation.

Prerequisites:
    pip install havona-sdk
    cp .env.example .env   # fill in your credentials
"""

import os
from dotenv import load_dotenv

load_dotenv()

from havona_sdk import HavonaClient, HavonaError, NotFoundError

client = HavonaClient.from_credentials(
    base_url=os.environ["HAVONA_API_URL"],
    auth0_domain=os.environ["AUTH0_DOMAIN"],
    auth0_audience=os.environ["AUTH0_AUDIENCE"],
    auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
    username=os.environ["HAVONA_EMAIL"],
    password=os.environ["HAVONA_PASSWORD"],
)

# --- Service health --------------------------------------------------

print("Agent registry service status:")
try:
    svc = client.agents.status()
    connected = svc.get("connected") or svc.get("blockchain_connected", False)
    print(f"  connected       = {connected}")
    print(f"  contractAddress = {svc.get('contractAddress') or svc.get('contract_address', 'n/a')}")
    print(f"  totalAgents     = {svc.get('totalAgents') or svc.get('total_agents', 0)}")
except HavonaError as e:
    print(f"  Error: {e}")

# --- List agents ------------------------------------------------------

print("\nRegistered agents:")
try:
    agents = client.agents.list()
    if not agents:
        print("  No agents registered yet.")
    for agent in agents:
        print(f"  [{agent.id}] {agent.name or '(unnamed)':30s} type={agent.agent_type}  wallet={agent.wallet or 'n/a'}")
except HavonaError as e:
    print(f"  Error: {e}")
    agents = []

# --- Reputation for each agent ---------------------------------------

if agents:
    print("\nReputation scores:")
    for agent in agents:
        try:
            rep = client.agents.get_reputation(agent.id)
            avg = f"{rep.average_score:.2f}" if rep.average_score is not None else "n/a"
            print(f"  [{agent.id}] total_feedback={rep.total_feedback}  avg_score={avg}")
        except (HavonaError, NotFoundError) as e:
            print(f"  [{agent.id}] reputation unavailable: {e}")
