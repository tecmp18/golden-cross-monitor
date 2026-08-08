#!/usr/bin/env python3
"""
Golden Cross Monitor — Turtle SMA v2.0 Health Check
Checks whether the 100/350 SMA golden cross is still intact for watchlist stocks.
Flags Rule 2.1 (reduce) and Rule 2.2 (death cross / full exit) signals.
Outputs to status.md for GitHub-native monitoring.
"""

import sys
import json
import logging
import concurrent.futures
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

# Suppress yfinance noise (404s, delisted warnings)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


# ─── Configuration ───────────────────────────────────────────────────────────

SMA_FAST = 100
SMA_SLOW = 350
RSI_PERIOD = 14
ADX_PERIOD = 14
EXTENSION_LIMIT = 15.0  # percent above SMA_FAST
HISTORY_DAYS = 500       # enough for 350 SMA to stabilize


# ─── Indicator calculations ─────────────────────────────────────────────────

def calc_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr)

    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
    adx = dx.ewm(alpha=1 / period, min_periods=period).mean()
    return adx, plus_di, minus_di


# ─── Core scan logic ────────────────────────────────────────────────────────

def scan_stock(symbol: str) -> dict:
    """Fetch data and evaluate golden cross health for one stock."""
    result = {
        "symbol": symbol.replace(".NS", ""),
        "ns_symbol": symbol,
        "status": "ERROR",
        "ltp": None,
        "sma50": None,
        "sma100": None,
        "sma200": None,
        "sma350": None,
        "classic_gc": None,
        "rsi": None,
        "adx": None,
        "plus_di": None,
        "minus_di": None,
        "extension_pct": None,
        "golden_cross": None,
        "rule_2_1": False,
        "rule_2_2": False,
        "alerts": [],
        "error": None,
    }

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{HISTORY_DAYS}d", interval="1d")

        # Drop rows where OHLC data is missing
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

        if df.empty or len(df) < SMA_SLOW + 10:
            result["error"] = f"Insufficient data ({len(df)} clean bars, need {SMA_SLOW + 10}+)"
            return result

        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        sma100 = calc_sma(close, SMA_FAST)
        sma350 = calc_sma(close, SMA_SLOW)
        sma50 = calc_sma(close, 50)
        sma200 = calc_sma(close, 200)
        rsi = calc_rsi(close, RSI_PERIOD)
        adx, plus_di, minus_di = calc_adx(high, low, close, ADX_PERIOD)

        # Latest values — guard against residual NaN
        ltp = close.iloc[-1]
        s100_raw = sma100.iloc[-1]
        s350_raw = sma350.iloc[-1]

        if pd.isna(ltp) or pd.isna(s100_raw) or pd.isna(s350_raw):
            result["error"] = f"SMA not ready (have {len(df)} bars, SMA350 needs {SMA_SLOW}+ non-NaN)"
            return result

        ltp = round(ltp, 2)
        s50 = round(sma50.iloc[-1], 2) if not pd.isna(sma50.iloc[-1]) else None
        s100 = round(s100_raw, 2)
        s200 = round(sma200.iloc[-1], 2) if not pd.isna(sma200.iloc[-1]) else None
        s350 = round(s350_raw, 2)
        rsi_val = round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 0.0
        adx_val = round(adx.iloc[-1], 2) if not pd.isna(adx.iloc[-1]) else 0.0
        pdi = round(plus_di.iloc[-1], 2) if not pd.isna(plus_di.iloc[-1]) else 0.0
        mdi = round(minus_di.iloc[-1], 2) if not pd.isna(minus_di.iloc[-1]) else 0.0

        result["ltp"] = ltp
        result["sma50"] = s50
        result["sma100"] = s100
        result["sma200"] = s200
        result["sma350"] = s350
        result["rsi"] = rsi_val
        result["adx"] = adx_val
        result["plus_di"] = pdi
        result["minus_di"] = mdi

        # Classic 50/200 golden cross
        classic_gc = (s50 is not None and s200 is not None and s50 > s200)
        result["classic_gc"] = classic_gc

        # Golden cross check
        golden = s100 > s350
        result["golden_cross"] = golden

        # Extension
        ext_pct = round(((ltp - s100) / s100) * 100, 2) if s100 > 0 else 0
        result["extension_pct"] = ext_pct

        # ── Status classification ────────────────────────────────────────

        # Rule 2.2 — Death Cross (full exit)
        if not golden:
            result["rule_2_2"] = True
            result["status"] = "🔴 DEATH CROSS"
            result["alerts"].append("100 SMA < 350 SMA — full exit signal")

            # Estimate how long ago the death cross happened
            cross_diff = sma100 - sma350
            cross_series = cross_diff.dropna()
            cross_sign = np.sign(cross_series)
            cross_changes = cross_sign.diff().fillna(0)
            death_crosses = cross_changes[cross_changes == -2]
            if not death_crosses.empty:
                last_dc = death_crosses.index[-1]
                days_ago = (df.index[-1] - last_dc).days
                result["alerts"].append(f"Death cross occurred ~{days_ago} days ago")
            return result

        # Rule 2.1 — Price below SMA100 + RSI < 50 (reduce)
        price_below_100 = ltp < s100
        rsi_below_50 = rsi_val < 50

        if price_below_100 and rsi_below_50:
            result["rule_2_1"] = True
            result["status"] = "🟠 REDUCE"
            result["alerts"].append("Price < 100 SMA AND RSI < 50 — reduce 50%")
        elif price_below_100:
            result["status"] = "🟡 CAUTION"
            result["alerts"].append("Price below 100 SMA but RSI still above 50")
        elif ext_pct > EXTENSION_LIMIT:
            result["status"] = "🟡 EXTENDED"
            result["alerts"].append(f"Price {ext_pct}% above 100 SMA (>{EXTENSION_LIMIT}% limit)")
        else:
            result["status"] = "🟢 HEALTHY"

        # Additional diagnostics
        if not classic_gc:
            result["alerts"].append("50/200 cross not active — weaker confirmation")
        if adx_val < 28:
            result["alerts"].append(f"ADX {adx_val} < 28 — trend weakening")
        if mdi > pdi:
            result["alerts"].append("-DI > +DI — bearish directional bias")

    except Exception as e:
        result["error"] = str(e)

    return result


# ─── Nifty 500 market check (S4) ────────────────────────────────────────────

def check_market() -> dict:
    """Check Nifty 500 SMA health."""
    try:
        df = yf.Ticker("^CRSLDX").history(period=f"{HISTORY_DAYS}d", interval="1d")
        df = df.dropna(subset=["Close"])
        if df.empty or len(df) < SMA_SLOW + 10:
            return {"signal": "?", "note": "Insufficient Nifty 500 data"}

        close = df["Close"]
        s100 = calc_sma(close, SMA_FAST).iloc[-1]
        s350 = calc_sma(close, SMA_SLOW).iloc[-1]
        ltp = close.iloc[-1]

        if pd.isna(s100) or pd.isna(s350) or pd.isna(ltp):
            return {"signal": "?", "note": "Nifty 500 SMA data incomplete"}

        if ltp > s100 and ltp > s350:
            return {"signal": "✓", "note": "Nifty 500 above both SMAs — healthy"}
        elif ltp > s350:
            return {"signal": "⚠", "note": "Nifty 500 above 350 SMA only — proceed with caution"}
        else:
            return {"signal": "✗", "note": "Nifty 500 below both SMAs — hard block on new entries"}
    except Exception as e:
        return {"signal": "?", "note": f"Market check failed: {e}"}


# ─── Output ──────────────────────────────────────────────────────────────────

def generate_markdown(results: list, market: dict) -> str:
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")

    lines = [
        "# Golden Cross Monitor",
        "",
        f"**Last updated:** {now}",
        f"**Market (Nifty 500):** {market['signal']} {market['note']}",
        "",
        "---",
        "",
    ]

    # Summary table for all stocks
    lines.append("## Full Scan")
    lines.append("")
    lines.append("| Symbol | Status | LTP | SMA 100 | SMA 350 | 50/200 | RSI | ADX | Ext% | Alerts |")
    lines.append("|--------|--------|-----|---------|---------|--------|-----|-----|------|--------|")

    for r in results:
        if r["status"] == "ERROR":
            lines.append(f"| {r['symbol']} | ❌ ERROR | — | — | — | — | — | — | — | {r['error']} |")
            continue
        alert_str = "; ".join(r["alerts"]) if r["alerts"] else "—"
        gc50 = "✓" if r.get("classic_gc") else "✗"
        lines.append(
            f"| {r['symbol']} | {r['status']} | ₹{r['ltp']} "
            f"| ₹{r['sma100']} | ₹{r['sma350']} "
            f"| {gc50} | {r['rsi']} | {r['adx']} | {r['extension_pct']}% "
            f"| {alert_str} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Status Legend</summary>")
    lines.append("")
    lines.append("| Status | Meaning | Action |")
    lines.append("|--------|---------|--------|")
    lines.append("| 🟢 HEALTHY | Golden cross intact, price above 100 SMA | Hold / monitor |")
    lines.append("| 🟡 CAUTION | Price below 100 SMA but RSI > 50 | Watch closely |")
    lines.append("| 🟡 EXTENDED | Price >15% above 100 SMA | Not ideal for new entry |")
    lines.append("| 🟠 REDUCE | Price < 100 SMA AND RSI < 50 | Rule 2.1 — reduce 50% |")
    lines.append("| 🔴 DEATH CROSS | 100 SMA < 350 SMA | Rule 2.2 — full exit |")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def generate_json(results: list, market: dict) -> dict:
    """Generate machine-readable JSON for downstream tooling."""
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).isoformat()
    return {
        "updated": now,
        "market": market,
        "stocks": results,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    watchlist_path = Path(__file__).parent / "watchlist.txt"
    if not watchlist_path.exists():
        print("ERROR: watchlist.txt not found")
        sys.exit(1)

    symbols = []
    for line in watchlist_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            symbols.append(line)

    if not symbols:
        print("WARNING: watchlist.txt is empty (no symbols found)")
        # Still write empty status
        market = {"signal": "—", "note": "No stocks to scan"}
        results = []
    else:
        print(f"Scanning {len(symbols)} stocks...")
        market = check_market()
        print(f"  Market: {market['signal']} {market['note']}")

        results = []
        for sym in symbols:
            print(f"  Scanning {sym}...", end=" ", flush=True)
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(scan_stock, sym)
                    r = future.result(timeout=30)
            except concurrent.futures.TimeoutError:
                r = {
                    "symbol": sym.replace(".NS", ""), "ns_symbol": sym,
                    "status": "ERROR", "ltp": None, "sma100": None, "sma350": None,
                    "rsi": None, "adx": None, "plus_di": None, "minus_di": None,
                    "extension_pct": None, "golden_cross": None,
                    "rule_2_1": False, "rule_2_2": False,
                    "alerts": [], "error": f"Timed out after 30s",
                }
            except Exception as e:
                r = {
                    "symbol": sym.replace(".NS", ""), "ns_symbol": sym,
                    "status": "ERROR", "ltp": None, "sma100": None, "sma350": None,
                    "rsi": None, "adx": None, "plus_di": None, "minus_di": None,
                    "extension_pct": None, "golden_cross": None,
                    "rule_2_1": False, "rule_2_2": False,
                    "alerts": [], "error": str(e),
                }
            print(r["status"])
            results.append(r)

    # Write outputs
    out_dir = Path(__file__).parent
    md = generate_markdown(results, market)
    (out_dir / "status.md").write_text(md)
    print(f"\nWrote status.md")

    j = generate_json(results, market)
    (out_dir / "status.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"Wrote status.json")

    # Exit code: 1 if any death cross or reduce signal
    has_action = any(r["rule_2_1"] or r["rule_2_2"] for r in results)
    if has_action:
        print("\n⚠️  ACTION REQUIRED — check status.md for details")

    # Always exit 0 so the workflow doesn't fail on alerts
    sys.exit(0)


if __name__ == "__main__":
    main()
