#!/usr/bin/env python3
"""
rank_ring_by_age.py <tx_hash>

Outputs height-based GNH scores AND generates:
Plot: age_height vs gnh_score (saved as gnh_age_plot.png)
"""

import sys, math, requests, json
import pandas as pd
import matplotlib.pyplot as plt

DAEMON = "http://127.0.0.1:38081"
EPS = 1e-9

###############################################################################
# RPC WRAPPER
###############################################################################

def rpc(endpoint, payload):
    url = f"{DAEMON}/{endpoint}"
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    return r.json()

###############################################################################
# BLOCK HEADER FETCHING
###############################################################################

def get_block_ts(height, cache):
    """Fetch timestamp for a given block height."""
    if height in cache:
        return cache[height]

    j = rpc("json_rpc", {
        "jsonrpc": "2.0",
        "id": "0",
        "method": "get_block_header_by_height",
        "params": {"height": height}
    })

    ts = j["result"]["block_header"]["timestamp"]
    cache[height] = ts
    return ts

###############################################################################
# TX PARSING
###############################################################################

def get_tx_json(tx_hash):
    j = rpc("get_transactions", {
        "txs_hashes": [tx_hash],
        "decode_as_json": True
    })

    if j.get("status") != "OK":
        raise RuntimeError("get_transactions failed: " + str(j))

    tx_json = j["txs"][0]["as_json"]
    tx = json.loads(tx_json)
    tx_height = j["txs"][0]["block_height"]
    tx_ts = j["txs"][0]["block_timestamp"]

    return tx, tx_height, tx_ts

###############################################################################
# OUTPUT INDEX PROCESSING
###############################################################################

def cumulative(offsets):
    """Convert key_offsets → global output indices."""
    s = 0
    out = []
    for o in offsets:
        s += int(o)
        out.append(s)
    return out

def get_output_heights(globals_list):
    """Return output heights directly from get_outs."""
    payload = {"outputs": [{"amount": 0, "index": i} for i in globals_list]}
    j = rpc("get_outs", payload)
    outs = j["outs"]
    return [o["height"] for o in outs]

###############################################################################
# SCORING (HEIGHT-BASED GNH)
###############################################################################

def compute_norm_age(ages):
    """Normalize age using: norm_age = (max - age) / (max - min)"""
    if len(ages) == 0:
        return []

    mi = min(ages)
    ma = max(ages)

    if ma - mi < EPS:
        return [1.0] * len(ages)

    return [(ma - a) / (ma - mi) for a in ages]

###############################################################################
# PLOTTING
###############################################################################

def plot_age_vs_gnh(df):
    """Generate: age_height vs gnh_score plot."""
    plt.figure(figsize=(8, 5))
    plt.scatter(df["age_height"], df["gnh_score"])
    plt.xlabel("age_height (blocks)")
    plt.ylabel("gnh_score (0–1)")
    plt.title("GNH Score vs Age (in Blocks)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("gnh_age_plot.png")
    print("[+] Saved plot → gnh_age_plot.png")

###############################################################################
# MAIN
###############################################################################

def main(tx_hash):

    print(f"[+] Fetching TX: {tx_hash}")
    tx, spend_height, _ = get_tx_json(tx_hash)

    vins = [v for v in tx.get("vin", []) if "key" in v]
    if not vins:
        print("No key-type inputs in this transaction.")
        return

    key = vins[0]["key"]
    offsets = key["key_offsets"]
    globals_idx = cumulative(offsets)

    print(f"[+] Ring size = {len(globals_idx)}")
    print("[+] Fetching output heights via get_outs...")
    out_heights = get_output_heights(globals_idx)

    # Compute age in blocks
    ages = [(spend_height - h) for h in out_heights]

    # Normalize to GNH score
    norm_age = compute_norm_age(ages)

    df = pd.DataFrame({
        "global_index": globals_idx,
        "out_height": out_heights,
        "age_height": ages,
        "norm_age": norm_age
    })

    df["gnh_score"] = df["norm_age"]

    print("\n=== Ranking by gnh_score (using block-height age) ===")
    print(df.sort_values("gnh_score", ascending=False).to_string(index=False))

    df.to_csv("ring_age_height_scores.csv", index=False)
    print("\n[+] Saved → ring_age_height_scores.csv")

    # PLOT (age_height vs gnh_score)
    plot_age_vs_gnh(df)

###############################################################################

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rank_ring_by_age.py <tx_hash>")
        sys.exit(1)
    main(sys.argv[1])
