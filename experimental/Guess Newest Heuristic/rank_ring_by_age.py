#!/usr/bin/env python3
"""
Usage:
    python rank_ring_by_age.py <tx_hash>
"""

import sys, math, requests, json, time
import pandas as pd
import numpy as np

DAEMON = "http://127.0.0.1:38081"
EPS = 1e-9

###############################################################################
# RPC WRAPPER
###############################################################################

def rpc(endpoint, payload):
    """Generic RPC wrapper for Monero daemon."""
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

    try:
        j = rpc("json_rpc", {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "get_block_header_by_height",
            "params": {"height": height}
        })
    except Exception:
        cache[height] = None
        return None

    result = j.get("result")
    if not result:
        cache[height] = None
        return None

    ts = result["block_header"].get("timestamp")
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
    """Return list of output heights (None when unknown)."""
    payload = {"outputs": [{"amount": 0, "index": i} for i in globals_list]}
    j = rpc("get_outs", payload)
    outs = j.get("outs", [])
    return [o.get("height") for o in outs]

###############################################################################
# SCORING HEURISTICS
###############################################################################

def compute_scores_for_valid_ages(valid_ages):
    """Compute age-based scores for non-missing rows only."""
    scores = {}
    ages = list(valid_ages)

    if len(ages) == 0:
        for col in ["inv_age", "norm_age", "neglog", "softmax_norm_age"]:
            scores[col] = []
        return scores

    scores["inv_age"] = [1.0 / (a + 86400.0) for a in ages]

    mi, ma = min(ages), max(ages)
    if ma - mi < EPS:
        scores["norm_age"] = [1.0] * len(ages)
    else:
        scores["norm_age"] = [(ma - a) / (ma - mi) for a in ages]

    scores["neglog"] = [-math.log(a / 86400.0 + 1e-6) for a in ages]

    exps = [math.exp(s) for s in scores["norm_age"]]
    ssum = sum(exps) + EPS
    scores["softmax_norm_age"] = [e / ssum for e in exps]

    return scores

###############################################################################
# PRINT HELPERS
###############################################################################

def print_gnh_ranking(df):
    """Print only gnh_score ranking, always showing all 16 rows."""
    
    # Any missing values?
    missing_flag = df[["out_height", "out_timestamp", "age_seconds", "gnh_score"]].isnull().any().any()

    header = "=== Ranking by gnh_score"
    if missing_flag:
        header += " (missing shown as MISSING)"
    header += " ==="

    print("\n" + header)

    # Sort: highest score first, NaN always last
    df_sorted = df.sort_values("gnh_score", ascending=False, na_position="last")

    # Fill missing for printing only
    print(df_sorted.fillna("MISSING").to_string(index=False))


###############################################################################
# MAIN
###############################################################################

def main(tx_hash):
    print(f"[+] Fetching TX {tx_hash}")
    tx, tx_height, tx_ts = get_tx_json(tx_hash)

    vins = [v for v in tx.get("vin", []) if "key" in v]
    if not vins:
        print("No key-type inputs in this transaction.")
        return

    key = vins[0]["key"]
    offsets = key["key_offsets"]
    globals_idx = cumulative(offsets)

    print(f"[+] Ring size: {len(globals_idx)}")
    print("[+] Fetching output heights...")
    heights = get_output_heights(globals_idx)

    block_cache = {}
    timestamps = []

    print("[+] Fetching block timestamps...")
    for i, h in enumerate(heights):
        if h is None:
            timestamps.append(None)
        else:
            timestamps.append(get_block_ts(h, block_cache))

        if i % 10 == 0:
            print(f"  ... {i+1}/{len(heights)}")

    ages = []
    for ts in timestamps:
        ages.append(max(0, tx_ts - ts) if ts is not None else None)

    df = pd.DataFrame({
        "global_index": globals_idx,
        "out_height": heights,
        "out_timestamp": timestamps,
        "age_seconds": ages
    })

    df = df.replace({None: np.nan})

    valid_mask = df["age_seconds"].notnull()
    valid_ages = df.loc[valid_mask, "age_seconds"].astype(float).tolist()

    scores = compute_scores_for_valid_ages(valid_ages)

    for col in ["inv_age", "norm_age", "neglog", "softmax_norm_age"]:
        df[col] = np.nan

    if len(valid_ages) > 0:
        df.loc[valid_mask, "inv_age"] = scores["inv_age"]
        df.loc[valid_mask, "norm_age"] = scores["norm_age"]
        df.loc[valid_mask, "neglog"] = scores["neglog"]
        df.loc[valid_mask, "softmax_norm_age"] = scores["softmax_norm_age"]

        df.loc[valid_mask, "gnh_score"] = df.loc[valid_mask, "norm_age"]
        df.loc[valid_mask, "newest_rank"] = df.loc[valid_mask, "age_seconds"].rank(ascending=True)
    else:
        df["gnh_score"] = np.nan
        df["newest_rank"] = np.nan

    print_gnh_ranking(df)

    df.to_csv("ring_age_scores.csv", index=False)
    print("\n[+] Saved → ring_age_scores.csv")

###############################################################################

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rank_ring_by_age.py <tx_hash>")
        sys.exit(1)

    main(sys.argv[1])
