"""
03 — Extract structured data from a trade document PDF.

Demonstrates the two extraction pathways:

A) ETR document extraction (/api/etr/extract)
   For Electronic Trade Records: Commercial Invoice, Bill of Lading,
   Certificate of Origin.

B) Trade blotting extraction (/api/blotting/extract-pdf)
   For unstructured trade documents: email confirmations, PDFs, Excel.

Both pathways return an ExtractionResult. Use .to_trade_fields() to
convert the result into a payload for client.trades.create().

Prerequisites:
    pip install havona-sdk
    cp .env.example .env   # fill in your credentials
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from havona_sdk import HavonaClient, HavonaError, ExtractionResult

client = HavonaClient.from_credentials(
    base_url=os.environ["HAVONA_API_URL"],
    auth0_domain=os.environ["AUTH0_DOMAIN"],
    auth0_audience=os.environ["AUTH0_AUDIENCE"],
    auth0_client_id=os.environ["AUTH0_CLIENT_ID"],
    username=os.environ["HAVONA_EMAIL"],
    password=os.environ["HAVONA_PASSWORD"],
)

# --- List supported ETR document types --------------------------------

print("Supported ETR document types:")
for t in client.documents.supported_types():
    desc = f" — {t.description}" if t.description else ""
    print(f"  {t.id}{desc}")

# --- Pathway A: ETR document extraction ------------------------------
#
# Uncomment and point at a real PDF to run this section.
#
# pdf_path = "commercial_invoice.pdf"
#
# print(f"\nExtracting {pdf_path} as COMMERCIAL_INVOICE ...")
# try:
#     result = client.documents.extract(pdf_path, "COMMERCIAL_INVOICE")
#     print(f"  Confidence  : {result.confidence:.0%}" if result.confidence else "  Confidence: n/a")
#     print(f"  Document type: {result.document_type}")
#     print(f"  Extracted fields:")
#     for k, v in result.fields.items():
#         print(f"    {k}: {v}")
#
#     # Save the extracted data as a trade
#     trade_fields = result.to_trade_fields()
#     if trade_fields:
#         trade = client.trades.create(**trade_fields, status="DRAFT")
#         print(f"\n  Saved as trade: {trade.id}")
#     else:
#         print("\n  No trade fields extracted.")
# except HavonaError as e:
#     print(f"  Error: {e}")

# --- Pathway B: Trade blotting extraction ----------------------------
#
# Uncomment and point at a real document to run this section.
#
# doc_path = "email_confirmation.pdf"
#
# print(f"\nExtracting trade fields from {doc_path} ...")
# try:
#     result = client.documents.extract_trade(doc_path)
#     print(f"  Document type: {result.document_type}")
#     print(f"  Fields: {result.fields}")
#
#     trade_fields = result.to_trade_fields()
#     if trade_fields:
#         trade = client.trades.create(**trade_fields, status="DRAFT")
#         print(f"  Saved trade: {trade.id}")
# except HavonaError as e:
#     print(f"  Error: {e}")

print("\nUncomment sections above and provide a real PDF to run extraction.")
