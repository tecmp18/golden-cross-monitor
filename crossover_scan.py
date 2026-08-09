#!/usr/bin/env python3
"""
Nifty 500 — Two-Stage Golden Cross Scanner
============================================
Scans for stocks entering the two-stage scaling system with SMA direction filters:

ENTRY:
  Stage 1 (50%) — Price > 50 > 200, 200 < 350, 50 SMA rising
  Stage 2 (100%) — Price > 50 > 200 > 350, 50 & 200 SMA rising

SMA Direction:
  50 SMA rising  → current > 5 trading days ago
  200 SMA rising → current > 20 trading days ago
  350 SMA rising → current > 20 trading days ago
"""

import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ─────────────────────────────────────────────
# PARAMETERS
# ─────────────────────────────────────────────
DATA_PERIOD = "2y"
CROSS_LOOKBACK = 30

IST = ZoneInfo("Asia/Kolkata")


# ─────────────────────────────────────────────
# SMA DIRECTION
# ─────────────────────────────────────────────

def sma_rising(sma_series, lookback):
    """Check if SMA is rising: current value > value `lookback` bars ago."""
    if len(sma_series) <= lookback:
        return False
    current = sma_series.iloc[-1]
    past = sma_series.iloc[-1 - lookback]
    if pd.isna(current) or pd.isna(past):
        return False
    return current > past


# ─────────────────────────────────────────────
# STOCK ANALYSIS
# ─────────────────────────────────────────────

def analyze_stock(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=DATA_PERIOD)

        if df.empty or len(df) < 360:
            return None

        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['SMA_350'] = df['Close'].rolling(window=350).mean()

        df = df.dropna(subset=['SMA_50', 'SMA_200', 'SMA_350'])
        if len(df) < 21:
            return None

        latest = df.iloc[-1]
        close = latest['Close']
        sma50 = latest['SMA_50']
        sma200 = latest['SMA_200']
        sma350 = latest['SMA_350']

        # ── Cross checks ────────────────────────────────────────
        price_above_50 = close > sma50
        gc_50_200 = sma50 > sma200
        gc_200_350 = sma200 > sma350

        # ── SMA direction ───────────────────────────────────────
        r50 = sma_rising(df['SMA_50'], 5)
        r200 = sma_rising(df['SMA_200'], 20)
        r350 = sma_rising(df['SMA_350'], 20)

        # ── Stage classification ────────────────────────────────
        # Must have at minimum: Price > 50 > 200
        if not (price_above_50 and gc_50_200):
            return None

        if gc_200_350:
            # Fully stacked — check if qualifies for Stage 2
            if r50 and r200:
                stage = "Stage 2"
                stage_label = "🟢 STAGE 2 — Full position (100%)"
            else:
                stage = "Hold"
                stage_label = "🟢 HOLD BOTH — stacked but SMAs not all rising"
        else:
            # 200 < 350 — check if qualifies for Stage 1
            if r50:
                stage = "Stage 1"
                stage_label = "🟡 STAGE 1 — Half position (50%)"
            else:
                stage = "Wait"
                stage_label = "⚪ WAIT — 50 SMA not rising"

        # ── Cross dates / freshness ─────────────────────────────
        cross_50_200 = df['SMA_50'] - df['SMA_200']
        sign_50_200 = np.sign(cross_50_200)
        changes_50_200 = sign_50_200.diff().fillna(0)
        gc_events_50_200 = changes_50_200[changes_50_200 == 2]

        t1_cross_date = None
        t1_cross_age = None
        t1_fresh = False
        if not gc_events_50_200.empty:
            last_gc = gc_events_50_200.index[-1]
            t1_cross_age = (df.index[-1] - last_gc).days
            t1_cross_date = last_gc.strftime("%Y-%m-%d")
            if t1_cross_age <= CROSS_LOOKBACK:
                t1_fresh = True

        t2_cross_date = None
        t2_cross_age = None
        t2_fresh = False
        if gc_200_350:
            cross_200_350 = df['SMA_200'] - df['SMA_350']
            sign_200_350 = np.sign(cross_200_350)
            changes_200_350 = sign_200_350.diff().fillna(0)
            gc_events_200_350 = changes_200_350[changes_200_350 == 2]

            if not gc_events_200_350.empty:
                last_gc = gc_events_200_350.index[-1]
                t2_cross_age = (df.index[-1] - last_gc).days
                t2_cross_date = last_gc.strftime("%Y-%m-%d")
                if t2_cross_age <= CROSS_LOOKBACK:
                    t2_fresh = True

        # Freshness label
        if stage == "Stage 2" and t2_fresh:
            freshness = "🆕 Fresh T2"
        elif stage == "Stage 1" and t1_fresh:
            freshness = "🆕 Fresh T1"
        else:
            freshness = "Established"

        # Gap metrics
        gap_50_200 = round(((sma50 - sma200) / sma200) * 100, 2)
        gap_200_350 = round(((sma200 - sma350) / sma350) * 100, 2) if gc_200_350 else None
        price_vs_50 = round(((close - sma50) / sma50) * 100, 2)

        return {
            "symbol": symbol.replace(".NS", ""),
            "stage": stage,
            "stage_label": stage_label,
            "freshness": freshness,
            "ltp": round(close, 2),
            "sma50": round(sma50, 2),
            "sma200": round(sma200, 2),
            "sma350": round(sma350, 2),
            "sma50_rising": r50,
            "sma200_rising": r200,
            "sma350_rising": r350,
            "price_vs_50_pct": price_vs_50,
            "gap_50_200_pct": gap_50_200,
            "gap_200_350_pct": gap_200_350,
            "t1_cross_date": t1_cross_date,
            "t1_cross_age": t1_cross_age,
            "t2_cross_date": t2_cross_date,
            "t2_cross_age": t2_cross_age,
            "t1_fresh": t1_fresh,
            "t2_fresh": t2_fresh,
        }

    except Exception as e:
        print(f"  ✗ Error analyzing {symbol}: {e}")
        return None


# ─────────────────────────────────────────────
# SCANNER
# ─────────────────────────────────────────────

def load_stock_list(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"✗ Stock list not found: {filepath}")
        sys.exit(1)
    symbols = [line.strip() for line in path.read_text().splitlines()
               if line.strip() and not line.strip().startswith('#')]
    symbols = [s if s.endswith('.NS') else s + '.NS' for s in symbols]
    return symbols


def run_scan(symbols):
    results = []
    errors = 0
    total = len(symbols)

    print(f"\n{'='*60}")
    print(f"  TWO-STAGE GOLDEN CROSS SCANNER")
    print(f"  Stage 1: Price > 50↑ > 200, 200 < 350  (50%)")
    print(f"  Stage 2: Price > 50↑ > 200↑ > 350      (100%)")
    print(f"  Scanning {total} stocks")
    print(f"  {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    print(f"{'='*60}\n")

    for idx, symbol in enumerate(symbols, 1):
        print(f"  [{idx}/{total}] {symbol}...", end='\r')
        result = analyze_stock(symbol)
        if result:
            results.append(result)
        else:
            errors += 1

    s1 = [r for r in results if r["stage"] == "Stage 1"]
    s2 = [r for r in results if r["stage"] == "Stage 2"]
    hold = [r for r in results if r["stage"] == "Hold"]
    wait = [r for r in results if r["stage"] == "Wait"]
    print(f"\n\n  ✓ Scan complete.")
    print(f"  Stage 2: {len(s2)} | Stage 1: {len(s1)} | Hold: {len(hold)} | Wait: {len(wait)}")
    print(f"  Errors/no-data/no-qualify: {errors}\n")
    return results, errors


# ─────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────

def _direction(val):
    return "↑" if val else "↓"


def _table_row(r, show_t2=False):
    d50 = _direction(r['sma50_rising'])
    d200 = _direction(r['sma200_rising'])
    d350 = _direction(r['sma350_rising'])
    t1_age = f"{r['t1_cross_age']}d" if r['t1_cross_age'] is not None else "—"
    t1_date = r['t1_cross_date'] or "—"

    base = (f"| {r['symbol']} | ₹{r['ltp']} "
            f"| ₹{r['sma50']} {d50} | ₹{r['sma200']} {d200} | ₹{r['sma350']} {d350} "
            f"| {t1_date} | {t1_age}")

    if show_t2:
        t2_date = r['t2_cross_date'] or "—"
        t2_age = f"{r['t2_cross_age']}d" if r['t2_cross_age'] is not None else "—"
        base += f" | {t2_date} | {t2_age}"

    gap_200_350 = f"{r['gap_200_350_pct']}%" if r['gap_200_350_pct'] is not None else "—"
    base += f" | {r['gap_50_200_pct']}% | {gap_200_350} |"
    return base


def generate_markdown(results, total_scanned, errors):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    s1 = [r for r in results if r["stage"] == "Stage 1"]
    s2 = [r for r in results if r["stage"] == "Stage 2"]
    hold = [r for r in results if r["stage"] == "Hold"]
    wait = [r for r in results if r["stage"] == "Wait"]

    fresh_t1 = [r for r in results if r["t1_fresh"] and r["stage"] == "Stage 1"]
    fresh_t2 = [r for r in results if r["t2_fresh"] and r["stage"] == "Stage 2"]

    s1.sort(key=lambda r: (0 if r["t1_fresh"] else 1, r["t1_cross_age"] or 9999))
    s2.sort(key=lambda r: (0 if r["t2_fresh"] else 1, r["t2_cross_age"] or 9999))

    lines = [
        "# Two-Stage Golden Cross Scanner",
        "",
        f"**Last updated:** {now}",
        f"**Scanned:** {total_scanned} | "
        f"**Stage 2:** {len(s2)} | "
        f"**Stage 1:** {len(s1)} | "
        f"**Hold:** {len(hold)} | "
        f"**Wait:** {len(wait)} | "
        f"**Fresh T1:** {len(fresh_t1)} | "
        f"**Fresh T2:** {len(fresh_t2)} | "
        f"**Skipped:** {errors}",
        "",
        "↑ = SMA rising (50: 5d, 200/350: 20d) · ↓ = SMA falling",
        "",
        "---",
        "",
    ]

    # ── Fresh entries ───────────────────────────────────────
    if fresh_t1 or fresh_t2:
        lines.append(f"## 🆕 Fresh Entries (last {CROSS_LOOKBACK} trading days)")
        lines.append("")

        if fresh_t2:
            lines.append("### Add Tranche 2 — 200 just crossed above 350")
            lines.append("")
            lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |")
            lines.append("|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|")
            for r in fresh_t2:
                lines.append(_table_row(r, show_t2=True))
            lines.append("")

        if fresh_t1:
            lines.append("### Buy Tranche 1 — 50 just crossed above 200")
            lines.append("")
            lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |")
            lines.append("|--------|-----|--------|---------|---------|----------|--------|------------|-------------|")
            for r in fresh_t1:
                lines.append(_table_row(r, show_t2=False))
            lines.append("")

        lines.append("---")
        lines.append("")

    # ── Stage 2 ─────────────────────────────────────────────
    lines.append("## 🟢 Stage 2 — Full Position (Price > 50↑ > 200↑ > 350)")
    lines.append("")
    if s2:
        lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |")
        lines.append("|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|")
        for r in s2:
            lines.append(_table_row(r, show_t2=True))
    else:
        lines.append("*No stocks in Stage 2*")
    lines.append("")

    # ── Stage 1 ─────────────────────────────────────────────
    lines.append("## 🟡 Stage 1 — Half Position (Price > 50↑ > 200, 200 < 350)")
    lines.append("")
    if s1:
        lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |")
        lines.append("|--------|-----|--------|---------|---------|----------|--------|------------|-------------|")
        for r in s1:
            lines.append(_table_row(r, show_t2=False))
    else:
        lines.append("*No stocks in Stage 1*")
    lines.append("")

    # ── Hold (stacked but SMAs not all rising) ──────────────
    if hold:
        lines.append("## 🟢 Hold — Stacked but SMAs not all rising")
        lines.append("")
        lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |")
        lines.append("|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|")
        for r in hold:
            lines.append(_table_row(r, show_t2=True))
        lines.append("")

    # ── Wait (cross active but 50 SMA not rising) ───────────
    if wait:
        lines.append("## ⚪ Wait — Cross active but 50 SMA not rising")
        lines.append("")
        lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |")
        lines.append("|--------|-----|--------|---------|---------|----------|--------|------------|-------------|")
        for r in wait:
            lines.append(_table_row(r, show_t2=False))
        lines.append("")

    # ── Legend ───────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>System Rules</summary>")
    lines.append("")
    lines.append("| Status | Condition | Action | Position |")
    lines.append("|--------|-----------|--------|----------|")
    lines.append("| 🆕 Fresh T1 | 50/200 bullish cross ≤30 days | Candidate for T1 | — |")
    lines.append("| 🟡 Stage 1 | Price > 50 > 200, 200 < 350, 50↑ | Buy T1 | 50% |")
    lines.append("| 🆕 Fresh T2 | 200/350 bullish cross ≤30 days | Candidate for T2 | — |")
    lines.append("| 🟢 Stage 2 | Price > 50 > 200 > 350, 50↑ 200↑ | Add T2 | 100% |")
    lines.append("| ⚪ Wait | Cross active but SMA not rising | No action | — |")
    lines.append("")
    lines.append("**SMA Direction:** 50 SMA vs 5 days ago · 200/350 SMA vs 20 days ago")
    lines.append("")
    lines.append("**Exit Rules:**")
    lines.append("| | Exit trigger | Action |")
    lines.append("|--|-------------|--------|")
    lines.append("| T1 | 50 SMA crosses below 200 SMA | Sell tranche 1 |")
    lines.append("| T2 | 200 SMA crosses below 350 SMA | Sell tranche 2 |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    stock_list = Path(__file__).parent / "nifty500.txt"
    symbols = load_stock_list(stock_list)
    results, errors = run_scan(symbols)

    out_dir = Path(__file__).parent
    md = generate_markdown(results, len(symbols), errors)
    (out_dir / "crossovers.md").write_text(md)
    print(f"  Wrote crossovers.md")

    s1_count = len([r for r in results if r["stage"] == "Stage 1"])
    s2_count = len([r for r in results if r["stage"] == "Stage 2"])
    hold_count = len([r for r in results if r["stage"] == "Hold"])
    wait_count = len([r for r in results if r["stage"] == "Wait"])

    j = {
        "updated": datetime.now(IST).isoformat(),
        "total_scanned": len(symbols),
        "stage_1_count": s1_count,
        "stage_2_count": s2_count,
        "hold_count": hold_count,
        "wait_count": wait_count,
        "errors": errors,
        "stocks": results,
    }
    (out_dir / "crossovers.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"  Wrote crossovers.json")
