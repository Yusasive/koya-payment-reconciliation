#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (from the README):
  - Only the latest attempt (by `ts`) for each txn_id counts.
  - A payment is collected only if that latest attempt is `success`.
  - Skip lines that can't be parsed and events with no txn_id.
  - Amounts may arrive as numbers or as strings like "4,804.15".
"""
import json
from datetime import datetime


def parse_amount(value):
    """Accept 1234.5, "1234.5" or "1,234.50"."""
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", "").strip())


def parse_ts(value):
    """ISO 8601 UTC timestamp, e.g. 2026-09-21T15:30:26Z."""
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


latest = {}  # txn_id -> (timestamp, event)
skipped_lines = 0
skipped_no_id = 0

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            skipped_lines += 1
            continue
        if not isinstance(event, dict):
            skipped_lines += 1
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            skipped_no_id += 1
            continue

        ts = parse_ts(event["ts"])
        current = latest.get(txn_id)
        if current is None or ts > current[0]:
            latest[txn_id] = (ts, event)

total = 0.0
count = 0
for _, event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

print(f"Skipped {skipped_lines} unreadable lines and {skipped_no_id} events without a txn_id.")
print(f"Unique transactions: {len(latest)}")

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Total collected: NGN {total:,.2f}")
    print(f"Your code: KOYA-{round(total)}")