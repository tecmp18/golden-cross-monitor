#!/usr/bin/env python3
"""
Nifty 500 Golden Crossover Scanner
===================================
Scans all stocks in nifty500.txt for active golden crosses (100 SMA > 350 SMA).
Highlights fresh crosses (within last 30 trading days).
Designed to run weekly via GitHub Actions.
Outputs to crossovers.md and crossovers.json.
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
RSI_PERIOD = 14
ADX_PERIOD = 14
DATA_PERIOD = "2y"          # same as turtle scanner
CROSS_LOOKBACK = 30         # flag crosses within last N trading days

IST = ZoneInfo("Asia/Kolkata")


# ─────────────────────────────────────────────
# INDICATOR CALCULATIONS
# ─────────────────────────────────────────────

def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_adx(high, low, close, period=14):
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


# ─────────────────────────────────────────────
# STOCK ANALYSIS
# ─────────────────────────────────────────────

def analyze_stock(symbol):
    """
    Check if a stock has an active golden cross.
    Returns dict with signal details, or None.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=DATA_PERIOD)

        if df.empty or len(df) < SMA_SLOW + 10:
            return None

        # Compute indicators
        df['SMA_100'] = df['Close'].rolling(window=SMA_FAST).mean()
        df['SMA_350'] = df['Close'].rolling(window=SMA_SLOW).mean()
        df['RSI'] = calc_rsi(df['Close'], RSI_PERIOD)
        df['ADX'], df['Plus_DI'], df['Minus_DI'] = calc_adx(
            df['High'], df['Low'], df['Close'], ADX_PERIOD
        )

        # Drop rows where indicators aren't ready
        df = df.dropna(subset=['SMA_100', 'SMA_350', 'RSI', 'ADX'])
        if len(df) < 2:
            return None

        latest = df.iloc[-1]
        close = latest['Close']
        sma100 = latest['SMA_100']
        sma350 = latest['SMA_350']

        # Only interested in golden cross (100 > 350)
        if sma100 <= sma350:
            return None

        rsi_val = latest['RSI']
        adx_val = latest['ADX']
        pdi = latest['Plus_DI']
        mdi = latest['Minus_DI']
        ext_pct = round(((close - sma100) / sma100) * 100, 2)
        price_above_both = close > sma100 and close > sma350

        # Find when the golden cross happened
        cross_diff = df['SMA_100'] - df['SMA_350']
        cross_sign = np.sign(cross_diff)
        cross_changes = cross_sign.diff().fillna(0)
        golden_crosses = cross_changes[cross_changes == 2]

        cross_age = None
        cross_date = None
        freshness = "Established"
        if not golden_crosses.empty:
            last_gc = golden_crosses.index[-1]
            cross_age = (df.index[-1] - last_gc).days
            cross_date = last_gc.strftime("%Y-%m-%d")
            if cross_age <= CROSS_LOOKBACK:
                freshness = "🆕 Fresh"

        return {
            "symbol": symbol.replace(".NS", ""),
            "ltp": round(close, 2),
            "sma100": round(sma100, 2),
            "sma350": round(sma350, 2),
            "rsi": round(rsi_val, 2),
            "adx": round(adx_val, 2),
            "plus_di": round(pdi, 2),
            "minus_di": round(mdi, 2),
            "extension_pct": ext_pct,
            "cross_date": cross_date,
            "cross_age_days": cross_age,
            "freshness": freshness,
            "price_above_both": price_above_both,
            "di_bullish": pdi > mdi,
        }

    except Exception as e:
        print(f"  ✗ Error analyzing {symbol}: {e}")
        return None


# ─────────────────────────────────────────────
# SCANNER (matches turtle scanner pattern)
# ─────────────────────────────────────────────

def load_stock_list(filepath):
    """Load stock symbols from file, one per line."""
    path = Path(filepath)
    if not path.exists():
        print(f"✗ Stock list not found: {filepath}")
        sys.exit(1)

    symbols = [line.strip() for line in path.read_text().splitlines()
               if line.strip() and not line.strip().startswith('#')]
    symbols = [s if s.endswith('.NS') else s + '.NS' for s in symbols]
    return symbols


def run_scan(symbols):
    """Scan all symbols for golden crosses. Returns list of signal dicts."""
    results = []
    errors = 0
    total = len(symbols)

    print(f"\n{'='*60}")
    print(f"  GOLDEN CROSSOVER SCANNER")
    print(f"  SMA {SMA_FAST} > SMA {SMA_SLOW} | Fresh window: {CROSS_LOOKBACK}d")
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

    print(f"\n\n  ✓ Scan complete. {len(results)} golden cross(es) found.")
    print(f"  ✗ Errors/no-data/no-cross: {errors}\n")
    return results, errors


# ─────────────────────────────────────────────
# OUTPUT
# ─────────────────────────────────────────────

def generate_markdown(results, total_scanned, errors):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    # Sort: fresh crosses first, then by cross age (newest first)
    results.sort(key=lambda r: (
        0 if r["freshness"].startswith("🆕") else 1,
        r["cross_age_days"] if r["cross_age_days"] is not None else 9999,
    ))

    fresh = [r for r in results if r["freshness"].startswith("🆕")]

    lines = [
        "# Nifty 500 — Golden Crossover Scan",
        "",
        f"**Last updated:** {now}",
        f"**Scanned:** {total_scanned} stocks | "
        f"**Golden cross active:** {len(results)} | "
        f"**Fresh ({CROSS_LOOKBACK}d):** {len(fresh)} | "
        f"**Errors/skipped:** {errors}",
        "",
        "---",
        "",
    ]

    if fresh:
        lines.append(f"## 🆕 Fresh Golden Crosses (last {CROSS_LOOKBACK} trading days)")
        lines.append("")
        lines.append("| Symbol | LTP | SMA 100 | SMA 350 | Cross Date | Age | RSI | ADX | +DI>-DI | Ext% | Price>SMAs |")
        lines.append("|--------|-----|---------|---------|------------|-----|-----|-----|---------|------|-----------|")
        for r in fresh:
            di_flag = "✓" if r["di_bullish"] else "✗"
            pa_flag = "✓" if r["price_above_both"] else "✗"
            lines.append(
                f"| {r['symbol']} | ₹{r['ltp']} | ₹{r['sma100']} | ₹{r['sma350']} "
                f"| {r['cross_date']} | {r['cross_age_days']}d "
                f"| {r['rsi']} | {r['adx']} | {di_flag} | {r['extension_pct']}% | {pa_flag} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## All Active Golden Crosses")
    lines.append("")
    lines.append("| Symbol | LTP | SMA 100 | SMA 350 | Cross Date | Age | RSI | ADX | +DI>-DI | Ext% | Price>SMAs |")
    lines.append("|--------|-----|---------|---------|------------|-----|-----|-----|---------|------|-----------|")

    for r in results:
        di_flag = "✓" if r["di_bullish"] else "✗"
        pa_flag = "✓" if r["price_above_both"] else "✗"
        age_str = f"{r['cross_age_days']}d" if r["cross_age_days"] is not None else "—"
        cross_str = r["cross_date"] or "—"
        lines.append(
            f"| {r['symbol']} | ₹{r['ltp']} | ₹{r['sma100']} | ₹{r['sma350']} "
            f"| {cross_str} | {age_str} "
            f"| {r['rsi']} | {r['adx']} | {di_flag} | {r['extension_pct']}% | {pa_flag} |"
        )

    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    stock_list = Path(__file__).parent / "nifty500.txt"
    symbols = load_stock_list(stock_list)
    results, errors = run_scan(symbols)

    # Write outputs
    out_dir = Path(__file__).parent
    md = generate_markdown(results, len(symbols), errors)
    (out_dir / "crossovers.md").write_text(md)
    print(f"  Wrote crossovers.md")

    j = {
        "updated": datetime.now(IST).isoformat(),
        "total_scanned": len(symbols),
        "golden_cross_count": len(results),
        "errors": errors,
        "stocks": results,
    }
    (out_dir / "crossovers.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"  Wrote crossovers.json")
