#!/usr/bin/env python3
import requests
from collections import defaultdict
import sys

API = "http://127.0.0.1:5000"

def log(msg):
    print(f"[LOG] {msg}")

def fetch_recent(count):
    url = f"{API}/api/transaction-blocks/{count}"
    log(f"Fetching recent transaction blocks: {url}")
    try:
        r = requests.get(url, timeout=5)
        log(f"Status code: {r.status_code}")
        return r.json()
    except Exception as e:
        log(f"Error connecting to API: {e}")
        return {}

def fetch_tx(tx_hash):
    url = f"{API}/api/transaction/{tx_hash}"
    log(f"Fetching TX: {url}")
    try:
        r = requests.get(url, timeout=5)
        log(f"TX status: {r.status_code}")
        return r.json()
    except Exception as e:
        log(f"Error fetching TX {tx_hash}: {e}")
        return {}

def analyze(count=200):
    log(f"Starting ring-appearance scan for last {count} tx blocks...")
    ring_freq = defaultdict(int)
    tx_map = defaultdict(set)

    blocks = fetch_recent(count)

    if not blocks:
        log("ERROR: /api/transaction-blocks returned NOTHING.")
        return ring_freq, tx_map

    if "blocks" not in blocks:
        log("ERROR: API JSON does NOT contain 'blocks' key.")
        log(f"Raw JSON = {blocks}")
        return ring_freq, tx_map

    log(f"Found {len(blocks['blocks'])} blocks with transactions.")

    for blk_index, block in enumerate(blocks["blocks"], start=1):
        log(f"\n--- Block {blk_index}/{len(blocks['blocks'])} ---")
        log(f"Height: {block.get('height')}")
        log(f"TX Count: {len(block.get('tx_hashes', []))}")

        for tx_hash in block.get("tx_hashes", []):
            log(f"\nProcessing TX: {tx_hash}")
            tx = fetch_tx(tx_hash)

            if not tx:
                log("TX API returned EMPTY response.")
                continue

            ring_sigs = tx.get("ring_signatures")
            if ring_sigs is None:
                log("No 'ring_signatures' field in TX JSON.")
                log(f"TX JSON: {tx}")
                continue

            log(f"Found {len(ring_sigs)} ring signatures")

            for ring in ring_sigs:
                abs_offsets = ring.get("absolute_offsets", [])
                log(f"Ring has {len(abs_offsets)} decoys")

                if len(abs_offsets) == 0:
                    log("    ❌ absolute_offsets EMPTY; skipping.")
                    continue

                for g in abs_offsets:
                    ring_freq[g] += 1
                    tx_map[g].add(tx_hash)
                    log(f"+ Count[{g}] now = {ring_freq[g]}")

    log("\n=== FINISHED SCAN ===")
    return ring_freq, tx_map


if __name__ == "__main__":
    count = 200
    if len(sys.argv) > 1:
        count = int(sys.argv[1])

    ring_freq, tx_map = analyze(count)

    print("\n=== Most Repeated Ring Members ===")
    if not ring_freq:
        print("No ring members counted at all — see logs above!")
    else:
        for g, c in sorted(ring_freq.items(), key=lambda x: -x[1])[:20]:
            print(f"Global output {g} appears {c} times → TXs {list(tx_map[g])[:5]} ...")
