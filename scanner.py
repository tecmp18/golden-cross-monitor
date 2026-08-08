#!/usr/bin/env python3
"""
Golden Cross Monitor — Daily Watchlist Health Check
=====================================================
Checks dual golden cross health (100/350 + 50/200) for watchlist stocks.
Simple 3-state system for long-term holds:
  🟢 HEALTHY  — both 100>350 AND 50>200 active
  🟡 CAUTION  — either cross broken (one of the two)
  🔴 EXIT     — both 100<350 AND 50<200 broken
Outputs to status.md and status.json.
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
SMA_FAST = 100
SMA_SLOW = 350
DATA_PERIOD = "2y"

IST = ZoneInfo("Asia/Kolkata")


# ─────────────────────────────────────────────
# STOCK ANALYSIS
# ─────────────────────────────────────────────

def scan_stock(symbol):
    """Evaluate dual golden cross health for one stock."""
    result = {
        "symbol": symbol.replace(".NS", ""),
        "status": "ERROR",
        "ltp": None,
        "sma50": None,
        "sma100": None,
        "sma200": None,
        "sma350": None,
        "turtle_gc": None,
        "classic_gc": None,
        "exit": False,
        "alerts": [],
        "error": None,
    }

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=DATA_PERIOD)

        if df.empty or len(df) < SMA_SLOW + 10:
            result["error"] = f"Insufficient data ({len(df)} bars)"
            return result

        # Compute SMAs
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_100'] = df['Close'].rolling(window=SMA_FAST).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['SMA_350'] = df['Close'].rolling(window=SMA_SLOW).mean()

        # Drop rows where primary SMAs aren't ready
        df = df.dropna(subset=['SMA_100', 'SMA_350'])
        if len(df) < 2:
            result["error"] = "SMA not ready"
            return result

        latest = df.iloc[-1]
        close = latest['Close']
        s50 = latest['SMA_50']
        s100 = latest['SMA_100']
        s200 = latest['SMA_200']
        s350 = latest['SMA_350']

        result["ltp"] = round(close, 2)
        result["sma50"] = round(s50, 2) if not pd.isna(s50) else None
        result["sma100"] = round(s100, 2)
        result["sma200"] = round(s200, 2) if not pd.isna(s200) else None
        result["sma350"] = round(s350, 2)

        # ── Dual cross check ────────────────────────────────────────
        turtle_gc = s100 > s350
        classic_gc = (not pd.isna(s50) and not pd.isna(s200) and s50 > s200)

        result["turtle_gc"] = turtle_gc
        result["classic_gc"] = classic_gc

        # ── Status ───────────────────────────────────────────────────
        if not turtle_gc and not classic_gc:
            # 🔴 EXIT — both crosses broken
            result["status"] = "🔴 EXIT"
            result["exit"] = True
            result["alerts"].append("100<350 AND 50<200 — both crosses broken, exit position")

        elif not turtle_gc or not classic_gc:
            # 🟡 CAUTION — one cross broken
            result["status"] = "🟡 CAUTION"
            if not turtle_gc:
                result["alerts"].append("100 SMA < 350 SMA — turtle cross broken")
            if not classic_gc:
                result["alerts"].append("50 SMA < 200 SMA — classic cross broken")

        else:
            # 🟢 HEALTHY — both crosses active
            result["status"] = "🟢 HEALTHY"

    except Exception as e:
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────────
# MARKET CHECK
# ─────────────────────────────────────────────

def check_market():
    """Check Nifty 500 SMA health."""
    try:
        df = yf.Ticker("^CRSLDX").history(period=DATA_PERIOD)
        df = df.dropna(subset=["Close"])
        if df.empty or len(df) < SMA_SLOW + 10:
            return {"signal": "?", "note": "Insufficient Nifty 500 data"}

        close = df["Close"]
        s100 = close.rolling(window=SMA_FAST).mean().iloc[-1]
        s350 = close.rolling(window=SMA_SLOW).mean().iloc[-1]
        ltp = close.iloc[-1]

        if pd.isna(s100) or pd.isna(s350) or pd.isna(ltp):
            return {"signal": "?", "note": "Nifty 500 SMA data incomplete"}

        if ltp > s100 and ltp > s350:
            return {"signal": "✓", "note": "Nifty 500 above both SMAs — healthy"}
        elif ltp > s350:
            return {"signal": "⚠", "note": "Nifty 500 above 350 SMA only — caution"}
        else:
            return {"signal": "✗", "note": "Nifty 500 below both SMAs — avoid new entries"}
    except Exception as e:
        return {"signal": "?", "note": f"Market check failed: {e}"}


# ─────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────

def generate_markdown(results, market):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    lines = [
        "# Golden Cross Monitor",
        "",
        f"**Last updated:** {now}",
        f"**Market (Nifty 500):** {market['signal']} {market['note']}",
        "",
        "---",
        "",
        "## Watchlist",
        "",
        "| Symbol | Status | LTP | SMA 50 | SMA 100 | SMA 200 | SMA 350 | 100/350 | 50/200 | Alerts |",
        "|--------|--------|-----|--------|---------|---------|---------|---------|--------|--------|",
    ]

    for r in results:
        if r["status"] == "ERROR":
            lines.append(f"| {r['symbol']} | ❌ ERROR | — | — | — | — | — | — | — | {r['error']} |")
            continue

        turtle = "✓" if r.get("turtle_gc") else "✗"
        classic = "✓" if r.get("classic_gc") else "✗"
        s50 = f"₹{r['sma50']}" if r['sma50'] is not None else "—"
        s200 = f"₹{r['sma200']}" if r['sma200'] is not None else "—"
        alert_str = "; ".join(r["alerts"]) if r["alerts"] else "—"

        lines.append(
            f"| {r['symbol']} | {r['status']} | ₹{r['ltp']} "
            f"| {s50} | ₹{r['sma100']} | {s200} | ₹{r['sma350']} "
            f"| {turtle} | {classic} | {alert_str} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Status Legend</summary>")
    lines.append("")
    lines.append("| Status | Meaning | Action |")
    lines.append("|--------|---------|--------|")
    lines.append("| 🟢 HEALTHY | Both 100>350 AND 50>200 active | Hold |")
    lines.append("| 🟡 CAUTION | Either cross broken (one of the two) | Watch closely |")
    lines.append("| 🔴 EXIT | Both 100<350 AND 50<200 broken | Exit position |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    watchlist_path = Path(__file__).parent / "watchlist.txt"
    if not watchlist_path.exists():
        print("ERROR: watchlist.txt not found")
        sys.exit(1)

    symbols = []
    for line in watchlist_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if not line.endswith(".NS"):
                line = line + ".NS"
            symbols.append(line)

    if not symbols:
        print("WARNING: watchlist.txt is empty")
        market = {"signal": "—", "note": "No stocks to scan"}
        results = []
    else:
        print(f"Scanning {len(symbols)} stocks...")
        market = check_market()
        print(f"  Market: {market['signal']} {market['note']}")

        results = []
        for idx, sym in enumerate(symbols, 1):
            print(f"  [{idx}/{len(symbols)}] {sym}...", end='\r')
            r = scan_stock(sym)
            results.append(r)

    print(f"\n\n  ✓ Scan complete.\n")

    # Write outputs
    out_dir = Path(__file__).parent

    md = generate_markdown(results, market)
    (out_dir / "status.md").write_text(md)
    print(f"  Wrote status.md")

    j = {
        "updated": datetime.now(IST).isoformat(),
        "market": market,
        "stocks": results,
    }
    (out_dir / "status.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"  Wrote status.json")

    # Summary
    exits = [r for r in results if r.get("exit")]
    cautions = [r for r in results if r["status"].startswith("🟡")]
    if exits:
        print(f"\n  🔴 EXIT signals: {', '.join(r['symbol'] for r in exits)}")
    if cautions:
        print(f"  🟡 CAUTION: {', '.join(r['symbol'] for r in cautions)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
