#!/usr/bin/env python3
"""
Nifty 500 Golden Crossover Scanner
Scans all stocks in nifty500.txt for fresh or recent golden crosses (100 SMA > 350 SMA).
Designed to run weekly via GitHub Actions.
Outputs to crossovers.md.
"""

import sys
import json
import time
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
HISTORY_DAYS = 500
BATCH_SIZE = 10          # download tickers in batches to avoid rate limits
BATCH_SLEEP = 2          # seconds between batches
CROSS_LOOKBACK = 30      # flag crosses that happened within last N trading days
STOCK_TIMEOUT = 30       # seconds before giving up on a single stock


# ─── Indicator calculations (shared with scanner.py) ────────────────────────

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


# ─── Scan one stock ─────────────────────────────────────────────────────────

def scan_stock(symbol: str) -> dict | None:
    """Check if a stock has an active golden cross. Returns dict or None on error."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{HISTORY_DAYS}d", interval="1d")

        # Drop rows where OHLC data is missing
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

        if df.empty or len(df) < SMA_SLOW + 10:
            return None

        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        sma100 = calc_sma(close, SMA_FAST)
        sma350 = calc_sma(close, SMA_SLOW)
        rsi = calc_rsi(close, RSI_PERIOD)
        adx, plus_di, minus_di = calc_adx(high, low, close, ADX_PERIOD)

        s100 = sma100.iloc[-1]
        s350 = sma350.iloc[-1]

        # Skip if SMAs are NaN (insufficient clean data)
        if pd.isna(s100) or pd.isna(s350) or pd.isna(close.iloc[-1]):
            return None

        # Only interested in golden cross (100 > 350)
        if s100 <= s350:
            return None

        ltp = round(close.iloc[-1], 2)
        s100_r = round(s100, 2)
        s350_r = round(s350, 2)
        rsi_val = round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 0.0
        adx_val = round(adx.iloc[-1], 2) if not pd.isna(adx.iloc[-1]) else 0.0
        pdi = round(plus_di.iloc[-1], 2) if not pd.isna(plus_di.iloc[-1]) else 0.0
        mdi = round(minus_di.iloc[-1], 2) if not pd.isna(minus_di.iloc[-1]) else 0.0
        ext_pct = round(((ltp - s100) / s100) * 100, 2) if s100 > 0 else 0

        # Find when the golden cross happened
        cross_diff = sma100 - sma350
        cross_series = cross_diff.dropna()
        cross_sign = np.sign(cross_series)
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

        # Price position
        price_above_both = ltp > s100_r and ltp > s350_r

        return {
            "symbol": symbol.replace(".NS", ""),
            "ltp": ltp,
            "sma100": s100_r,
            "sma350": s350_r,
            "rsi": rsi_val,
            "adx": adx_val,
            "plus_di": pdi,
            "minus_di": mdi,
            "extension_pct": ext_pct,
            "cross_date": cross_date,
            "cross_age_days": cross_age,
            "freshness": freshness,
            "price_above_both": price_above_both,
            "di_bullish": pdi > mdi,
        }

    except Exception:
        return None


# ─── Output ──────────────────────────────────────────────────────────────────

def generate_markdown(results: list, total_scanned: int, errors: int) -> str:
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")

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


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    nifty_path = Path(__file__).parent / "nifty500.txt"
    if not nifty_path.exists():
        print("ERROR: nifty500.txt not found")
        sys.exit(1)

    symbols = []
    for line in nifty_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Ensure .NS suffix
            if not line.endswith(".NS"):
                line = line + ".NS"
            symbols.append(line)

    if not symbols:
        print("WARNING: nifty500.txt is empty")
        sys.exit(0)

    print(f"Scanning {len(symbols)} Nifty 500 stocks for golden crosses...")
    print(f"Batch size: {BATCH_SIZE}, sleep: {BATCH_SLEEP}s between batches\n")

    results = []
    errors = 0
    skipped = []

    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Batch {batch_num}/{total_batches}: {', '.join(s.replace('.NS','') for s in batch)}")

        for sym in batch:
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(scan_stock, sym)
                    r = future.result(timeout=STOCK_TIMEOUT)
            except concurrent.futures.TimeoutError:
                print(f"    ⏱ {sym} timed out after {STOCK_TIMEOUT}s — skipping")
                skipped.append(sym.replace(".NS", ""))
                errors += 1
                continue
            except Exception as e:
                print(f"    ✗ {sym} error: {e}")
                errors += 1
                continue

            if r is None:
                errors += 1
            else:
                results.append(r)

        if i + BATCH_SIZE < len(symbols):
            time.sleep(BATCH_SLEEP)

    if skipped:
        print(f"\nTimed out stocks: {', '.join(skipped)}")
    print(f"\nDone. Found {len(results)} stocks with active golden cross.")
    print(f"Errors/no-data/no-cross: {errors}")

    # Write outputs
    out_dir = Path(__file__).parent
    md = generate_markdown(results, len(symbols), errors)
    (out_dir / "crossovers.md").write_text(md)
    print(f"Wrote crossovers.md")

    j = {
        "updated": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "total_scanned": len(symbols),
        "golden_cross_count": len(results),
        "errors": errors,
        "stocks": results,
    }
    (out_dir / "crossovers.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"Wrote crossovers.json")

    sys.exit(0)


if __name__ == "__main__":
    main()
