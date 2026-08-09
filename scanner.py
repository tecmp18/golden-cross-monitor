#!/usr/bin/env python3
"""
Golden Cross Monitor — Daily Watchlist Health Check
=====================================================
Two-stage tranche monitoring with SMA direction:

  🟢 HOLD BOTH — 50>200 AND 200>350 (both tranches active)
  🟡 SELL T1   — 50<200 (sell tranche 1, keep T2 if 200>350)
  🟠 SELL T2   — 200<350 (sell tranche 2, keep T1 if 50>200)
  🔴 EXIT ALL  — 50<200 AND 200<350 (sell everything)

SMA Direction: 50 vs 5d ago · 200/350 vs 20d ago
"""

import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


DATA_PERIOD = "2y"
IST = ZoneInfo("Asia/Kolkata")


def sma_rising(sma_series, lookback):
    if len(sma_series) <= lookback:
        return False
    current = sma_series.iloc[-1]
    past = sma_series.iloc[-1 - lookback]
    if pd.isna(current) or pd.isna(past):
        return False
    return current > past


def scan_stock(symbol):
    result = {
        "symbol": symbol.replace(".NS", ""),
        "status": "ERROR",
        "ltp": None,
        "sma50": None, "sma200": None, "sma350": None,
        "gc_50_200": None, "gc_200_350": None,
        "sma50_rising": None, "sma200_rising": None, "sma350_rising": None,
        "exit_t1": False, "exit_t2": False,
        "alerts": [], "error": None,
    }

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=DATA_PERIOD)

        if df.empty or len(df) < 360:
            result["error"] = f"Insufficient data ({len(df)} bars)"
            return result

        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['SMA_350'] = df['Close'].rolling(window=350).mean()

        df = df.dropna(subset=['SMA_50', 'SMA_200', 'SMA_350'])
        if len(df) < 21:
            result["error"] = "SMA not ready"
            return result

        latest = df.iloc[-1]
        close = latest['Close']
        sma50 = latest['SMA_50']
        sma200 = latest['SMA_200']
        sma350 = latest['SMA_350']

        result["ltp"] = round(close, 2)
        result["sma50"] = round(sma50, 2)
        result["sma200"] = round(sma200, 2)
        result["sma350"] = round(sma350, 2)

        gc_50_200 = sma50 > sma200
        gc_200_350 = sma200 > sma350
        r50 = sma_rising(df['SMA_50'], 5)
        r200 = sma_rising(df['SMA_200'], 20)
        r350 = sma_rising(df['SMA_350'], 20)

        result["gc_50_200"] = gc_50_200
        result["gc_200_350"] = gc_200_350
        result["sma50_rising"] = r50
        result["sma200_rising"] = r200
        result["sma350_rising"] = r350

        # ── Status ───────────────────────────────────────────
        if gc_50_200 and gc_200_350:
            result["status"] = "🟢 HOLD BOTH"

        elif gc_50_200 and not gc_200_350:
            result["status"] = "🟠 SELL T2"
            result["exit_t2"] = True
            result["alerts"].append("200 < 350 — sell tranche 2")

        elif not gc_50_200 and gc_200_350:
            result["status"] = "🟡 SELL T1"
            result["exit_t1"] = True
            result["alerts"].append("50 < 200 — sell tranche 1")

        else:
            result["status"] = "🔴 EXIT ALL"
            result["exit_t1"] = True
            result["exit_t2"] = True
            result["alerts"].append("50<200 AND 200<350 — sell everything")

        # Direction warnings for held positions
        if result["status"] == "🟢 HOLD BOTH":
            if not r50:
                result["alerts"].append("50 SMA falling — momentum weakening")
            if not r200:
                result["alerts"].append("200 SMA falling — trend weakening")

    except Exception as e:
        result["error"] = str(e)

    return result


def check_market():
    try:
        df = yf.Ticker("^CRSLDX").history(period=DATA_PERIOD)
        df = df.dropna(subset=["Close"])
        if df.empty or len(df) < 360:
            return {"signal": "?", "note": "Insufficient Nifty 500 data"}

        close = df["Close"]
        s50 = close.rolling(window=50).mean().iloc[-1]
        s200 = close.rolling(window=200).mean().iloc[-1]
        ltp = close.iloc[-1]

        if pd.isna(s50) or pd.isna(s200) or pd.isna(ltp):
            return {"signal": "?", "note": "Nifty 500 SMA data incomplete"}

        if ltp > s50 and s50 > s200:
            return {"signal": "✓", "note": "Nifty 500: Price > 50 > 200 — healthy"}
        elif ltp > s200:
            return {"signal": "⚠", "note": "Nifty 500 above 200 SMA only — caution"}
        else:
            return {"signal": "✗", "note": "Nifty 500 below 200 SMA — avoid new entries"}
    except Exception as e:
        return {"signal": "?", "note": f"Market check failed: {e}"}


def _dir(val):
    if val is None:
        return "?"
    return "↑" if val else "↓"


def generate_markdown(results, market):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    lines = [
        "# Golden Cross Monitor",
        "",
        f"**Last updated:** {now}",
        f"**Market (Nifty 500):** {market['signal']} {market['note']}",
        "",
        "↑ = SMA rising (50: 5d, 200/350: 20d) · ↓ = SMA falling",
        "",
        "---",
        "",
        "## Watchlist",
        "",
        "| Symbol | Status | LTP | SMA 50 | SMA 200 | SMA 350 | 50/200 | 200/350 | Alerts |",
        "|--------|--------|-----|--------|---------|---------|--------|---------|--------|",
    ]

    for r in results:
        if r["status"] == "ERROR":
            lines.append(f"| {r['symbol']} | ❌ ERROR | — | — | — | — | — | — | {r['error']} |")
            continue

        d50 = _dir(r.get("sma50_rising"))
        d200 = _dir(r.get("sma200_rising"))
        d350 = _dir(r.get("sma350_rising"))
        t1 = "✓" if r.get("gc_50_200") else "✗"
        t2 = "✓" if r.get("gc_200_350") else "✗"
        alert_str = "; ".join(r["alerts"]) if r["alerts"] else "—"

        lines.append(
            f"| {r['symbol']} | {r['status']} | ₹{r['ltp']} "
            f"| ₹{r['sma50']} {d50} | ₹{r['sma200']} {d200} | ₹{r['sma350']} {d350} "
            f"| {t1} | {t2} | {alert_str} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>System Rules</summary>")
    lines.append("")
    lines.append("| Status | Condition | Action | Position |")
    lines.append("|--------|-----------|--------|----------|")
    lines.append("| 🟢 HOLD BOTH | 50>200 AND 200>350 | Hold both tranches | 100% |")
    lines.append("| 🟡 SELL T1 | 50<200 AND 200>350 | Sell tranche 1 | 50% |")
    lines.append("| 🟠 SELL T2 | 50>200 AND 200<350 | Sell tranche 2 | 50% |")
    lines.append("| 🔴 EXIT ALL | 50<200 AND 200<350 | Sell everything | 0% |")
    lines.append("")
    lines.append("**Entry (via weekly scan):**")
    lines.append("| Stage | Condition | Position |")
    lines.append("|-------|-----------|----------|")
    lines.append("| Stage 1 | Price > 50↑ > 200, 200 < 350 | 50% |")
    lines.append("| Stage 2 | Price > 50↑ > 200↑ > 350 | 100% |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


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

    sells = [r for r in results if r.get("exit_t1") or r.get("exit_t2")]
    if sells:
        for r in sells:
            print(f"  {r['status']}: {r['symbol']} — {'; '.join(r['alerts'])}")

    sys.exit(0)


if __name__ == "__main__":
    main()
