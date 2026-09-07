#!/usr/bin/env python3
"""
Patch A — Old vs New A/B comparison over the real nifty500.txt universe.
=========================================================================

Run this where network access to yfinance is available (local machine or
the existing GitHub Actions runner) — NOT in a sandboxed/offline environment.

Usage:
    python3 run_ab_comparison.py [path/to/nifty500.txt]

Design choice: each symbol's data is fetched ONCE, then both the OLD and
Patch A signal logic run against that same DataFrame. This guarantees any
difference in output is caused by the code change, not by market data
drift between two separate scan runs (or a second yfinance rate-limit hit).

Output:
  - ab_comparison_summary.json   — the before/after/delta metrics table
  - ab_comparison_detail.csv     — one row per symbol, both versions side by side
  - Printed report:
        * metrics table
        * OLD_ONLY / PATCH_A_ONLY / UNCHANGED candidate sets
        * every symbol with t2_before_t1 = True, full detail
        * freshness boundary check at 29 / 30 / 31 trading bars
"""

import sys
import json
import csv
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

DATA_PERIOD = "2y"
CROSS_LOOKBACK = 30


# ─────────────────────────────────────────────
# SHARED
# ─────────────────────────────────────────────
def sma_rising(sma_series, lookback):
    if len(sma_series) <= lookback:
        return False
    current = sma_series.iloc[-1]
    past = sma_series.iloc[-1 - lookback]
    if pd.isna(current) or pd.isna(past):
        return False
    return current > past


def load_stock_list(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"Stock list not found: {filepath}")
        sys.exit(1)
    symbols = [line.strip() for line in path.read_text().splitlines()
               if line.strip() and not line.strip().startswith('#')]
    symbols = [s if s.endswith('.NS') else s + '.NS' for s in symbols]
    return symbols


# ─────────────────────────────────────────────
# OLD LOGIC (faithful copy of production crossover_scan.py, unmodified)
# ─────────────────────────────────────────────
def compute_signals_old(df, symbol):
    latest = df.iloc[-1]
    close, sma50, sma200, sma350 = latest['Close'], latest['SMA_50'], latest['SMA_200'], latest['SMA_350']

    price_above_50 = close > sma50
    gc_50_200 = sma50 > sma200
    gc_200_350 = sma200 > sma350

    r50 = sma_rising(df['SMA_50'], 5)
    r200 = sma_rising(df['SMA_200'], 20)
    r350 = sma_rising(df['SMA_350'], 20)

    if not (price_above_50 and gc_50_200):
        return None, "not_qualified"

    if gc_200_350:
        stage = "Stage 2" if (r50 and r200) else "Hold"
    else:
        stage = "Stage 1" if r50 else "Wait"          # <-- the bug: no r200 check

    cross_50_200 = df['SMA_50'] - df['SMA_200']
    sign_50_200 = np.sign(cross_50_200)
    changes_50_200 = sign_50_200.diff().fillna(0)
    gc_events_50_200 = changes_50_200[changes_50_200 == 2]
    t1_cross_date, t1_cross_age, t1_fresh = None, None, False
    if not gc_events_50_200.empty:
        last_gc = gc_events_50_200.index[-1]
        t1_cross_age = (df.index[-1] - last_gc).days             # <-- calendar days
        t1_cross_date = last_gc.strftime("%Y-%m-%d")
        t1_fresh = t1_cross_age <= CROSS_LOOKBACK

    t2_cross_date, t2_cross_age, t2_fresh = None, None, False
    if gc_200_350:                                                # <-- gated, the other bug
        cross_200_350 = df['SMA_200'] - df['SMA_350']
        sign_200_350 = np.sign(cross_200_350)
        changes_200_350 = sign_200_350.diff().fillna(0)
        gc_events_200_350 = changes_200_350[changes_200_350 == 2]
        if not gc_events_200_350.empty:
            last_gc = gc_events_200_350.index[-1]
            t2_cross_age = (df.index[-1] - last_gc).days
            t2_cross_date = last_gc.strftime("%Y-%m-%d")
            t2_fresh = t2_cross_age <= CROSS_LOOKBACK

    return {
        "symbol": symbol.replace(".NS", ""), "stage": stage,
        "sma50_rising": r50, "sma200_rising": r200, "sma350_rising": r350,
        "gap_50_200_pct": round(((sma50 - sma200) / sma200) * 100, 2),
        "price_vs_50_pct": round(((close - sma50) / sma50) * 100, 2),
        "t1_cross_date": t1_cross_date, "t1_cross_age": t1_cross_age, "t1_fresh": t1_fresh,
        "t2_cross_date": t2_cross_date, "t2_cross_age": t2_cross_age, "t2_fresh": t2_fresh,
    }, "ok"


# ─────────────────────────────────────────────
# NEW LOGIC (Patch A) — import from the patched module
# ─────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from crossover_scan_patched import compute_signals as compute_signals_new  # noqa: E402


# ─────────────────────────────────────────────
# FETCH + RUN BOTH
# ─────────────────────────────────────────────
def fetch_and_prepare(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=DATA_PERIOD)
        if df.empty:
            return None, "no_data"
        if len(df) < 360:
            return None, "insufficient_history"
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['SMA_350'] = df['Close'].rolling(window=350).mean()
        df = df.dropna(subset=['SMA_50', 'SMA_200', 'SMA_350'])
        if len(df) < 21:
            return None, "insufficient_history"
        return df, "ok"
    except Exception as e:
        return None, f"exception: {type(e).__name__}: {e}"


def main():
    stock_list = sys.argv[1] if len(sys.argv) > 1 else "nifty500.txt"
    symbols = load_stock_list(stock_list)
    total = len(symbols)

    old_results, new_results = {}, {}
    skip_counts = {"no_data": 0, "insufficient_history": 0, "not_qualified": 0, "exception": 0}

    for idx, symbol in enumerate(symbols, 1):
        print(f"[{idx}/{total}] {symbol}...", end="\r")
        df, reason = fetch_and_prepare(symbol)
        if df is None:
            skip_counts[reason if reason in skip_counts else "exception"] += 1
            continue

        r_old, reason_old = compute_signals_old(df, symbol)
        r_new, reason_new = compute_signals_new(df, symbol)

        if reason_old != "ok" or reason_new != "ok":
            # should always agree on not_qualified since the gate before stage
            # classification (price_above_50, gc_50_200) is identical in both
            skip_counts["not_qualified"] += 1
            continue

        old_results[r_old["symbol"]] = r_old
        new_results[r_new["symbol"]] = r_new

    print(f"\n\nFetched and classified {len(old_results)} qualifying symbols "
          f"out of {total} scanned.\n")

    # ── Metrics table ────────────────────────────────────────
    def count_stage(results, stage):
        return sum(1 for r in results.values() if r["stage"] == stage)

    def count_fresh(results, stage, key):
        return sum(1 for r in results.values() if r["stage"] == stage and r[key])

    metrics = {
        "total_scanned": total,
        "errors": sum(skip_counts.values()) - skip_counts["not_qualified"],
        "stage_1": (count_stage(old_results, "Stage 1"), count_stage(new_results, "Stage 1")),
        "stage_2": (count_stage(old_results, "Stage 2"), count_stage(new_results, "Stage 2")),
        "fresh_t1": (count_fresh(old_results, "Stage 1", "t1_fresh"), count_fresh(new_results, "Stage 1", "t1_fresh")),
        "fresh_t2": (count_fresh(old_results, "Stage 2", "t2_fresh"), count_fresh(new_results, "Stage 2", "t2_fresh")),
        "t2_before_t1_true": (None, sum(1 for r in new_results.values() if r.get("t2_before_t1"))),
    }

    print("=" * 70)
    print(f"{'Metric':<20}{'Before':>10}{'Patch A':>12}{'Delta':>10}")
    print("-" * 70)
    for label, key in [("Stage 1", "stage_1"), ("Stage 2", "stage_2"),
                        ("Fresh T1", "fresh_t1"), ("Fresh T2", "fresh_t2")]:
        before, after = metrics[key]
        print(f"{label:<20}{before:>10}{after:>12}{after - before:>+10}")
    print(f"{'t2_before_t1=True':<20}{'—':>10}{metrics['t2_before_t1_true'][1]:>12}{'—':>10}")
    print("=" * 70)

    # ── Candidate set diff (qualifying = Stage 1 or Stage 2) ───
    old_candidates = {s for s, r in old_results.items() if r["stage"] in ("Stage 1", "Stage 2")}
    new_candidates = {s for s, r in new_results.items() if r["stage"] in ("Stage 1", "Stage 2")}

    old_only = sorted(old_candidates - new_candidates)
    new_only = sorted(new_candidates - old_candidates)
    unchanged = sorted(old_candidates & new_candidates)

    print(f"\nOLD_ONLY ({len(old_only)}) — expect these to show sma200_rising=False:")
    for s in old_only:
        r = old_results[s]
        expected = not r["sma200_rising"]
        flag = "" if expected else "  <-- UNEXPECTED, investigate"
        print(f"  {s:<15} sma50_rising={r['sma50_rising']}  sma200_rising={r['sma200_rising']}{flag}")

    print(f"\nPATCH_A_ONLY ({len(new_only)}) — should normally be empty; "
          f"Patch A should only REMOVE candidates via Strict, not add new ones:")
    for s in new_only:
        print(f"  {s:<15}  <-- UNEXPECTED, investigate")

    print(f"\nUNCHANGED: {len(unchanged)} symbols\n")

    # ── t2_before_t1 detail ─────────────────────────────────────
    whipsaw_flagged = [r for r in new_results.values() if r.get("t2_before_t1")]
    print(f"\nSymbols with t2_before_t1=True ({len(whipsaw_flagged)}):")
    for r in whipsaw_flagged:
        print(f"  {r['symbol']:<12} T1 cross={r['t1_cross_date']}  "
              f"prior T2 cross={r['t2_cross_date']}  "
              f"currently_stacked_200_350={'yes' if r['gap_200_350_pct'] is not None else 'no'}  "
              f"t1_fresh={r['t1_fresh']}  gap_50_200={r['gap_50_200_pct']}%")

    # ── Freshness boundary check ────────────────────────────────
    print("\nFreshness boundary check (Patch A, trading-bar age):")
    for age in (29, 30, 31):
        matches = [r["symbol"] for r in new_results.values() if r["t1_cross_age"] == age]
        if matches:
            expect_fresh = age <= CROSS_LOOKBACK
            for s in matches:
                actual_fresh = new_results[s]["t1_fresh"]
                ok = "OK" if actual_fresh == expect_fresh else "MISMATCH"
                print(f"  age={age}  {s:<12} fresh={actual_fresh}  expected={expect_fresh}  [{ok}]")

    # ── Write files ──────────────────────────────────────────────
    with open("ab_comparison_summary.json", "w") as f:
        json.dump({
            "metrics": {k: v for k, v in metrics.items()},
            "old_only": old_only,
            "patch_a_only": new_only,
            "unchanged_count": len(unchanged),
            "t2_before_t1_symbols": [r["symbol"] for r in whipsaw_flagged],
        }, f, indent=2, default=str)

    with open("ab_comparison_detail.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "old_stage", "new_stage", "old_t1_fresh", "new_t1_fresh",
                          "old_t1_cross_age", "new_t1_cross_age", "t2_before_t1"])
        for s in sorted(set(old_results) | set(new_results)):
            o, n = old_results.get(s), new_results.get(s)
            writer.writerow([
                s,
                o["stage"] if o else "—", n["stage"] if n else "—",
                o["t1_fresh"] if o else "—", n["t1_fresh"] if n else "—",
                o["t1_cross_age"] if o else "—", n["t1_cross_age"] if n else "—",
                n.get("t2_before_t1") if n else "—",
            ])

    print("\nWrote ab_comparison_summary.json and ab_comparison_detail.csv")


if __name__ == "__main__":
    main()
