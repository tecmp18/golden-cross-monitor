#!/usr/bin/env python3
"""
Nifty 500 — Two-Stage Golden Cross Scanner
============================================

Scans for stocks entering the two-stage scaling system with SMA direction filters:

ENTRY:
  Stage 1 (50%)  — Price > 50 > 200, 200 < 350, 50 SMA rising, 200 SMA rising
  Stage 2 (100%) — Price > 50 > 200 > 350, 50 & 200 SMA rising

SMA Direction:
  50 SMA rising  → current > 5 trading bars ago
  200 SMA rising → current > 20 trading bars ago
  350 SMA rising → current > 20 trading bars ago

Skip reasons (replaces the old flat "errors" count):
  no_data               — yfinance returned an empty dataframe
  insufficient_history  — fewer than 360 raw bars, or fewer than 21 bars
                           after dropping NaN SMA rows (too-new listing,
                           corporate-action gap, etc.)
  not_qualified         — real data, but doesn't meet Price > 50 > 200
                           (the normal, expected case for most of the
                           universe most of the time)
  exception             — a genuine script/API failure (network, parsing,
                           rate limit, bad symbol, etc.) — the only bucket
                           that actually warrants investigation

----------------------------------------------------------------------
PATCH A — VALIDATED / READY TO MERGE
----------------------------------------------------------------------
Three correctness fixes to the signal calculations, validated against
four synthetic edge cases and a full real-universe A/B run (493 symbols,
25/25 OLD_ONLY explanations confirmed, 0 unexpected PATCH_A_ONLY
additions, exact match on the 29/30/31 trading-bar freshness boundary).
No policy changes (5% extension gate, state taxonomy, T2 routing) are
included here — those are Patch B, applied separately against this
known-good baseline.

  1. T1 Strict gate — Stage 1 now requires BOTH r50 and r200 rising.
     Previously only r50 was checked; r200 was computed but unused,
     so the scanner silently ran "T1-Core" while every downstream
     manual review was applying "T1-Strict" by hand.

  2. Stack-independent T2 event detection — the 200/350 crossover scan
     now runs unconditionally over the full lookback window, not only
     `if gc_200_350` (i.e. only when currently stacked). This makes a
     prior T2 event visible even after it has since reverted, which is
     exactly the whipsaw pattern (precedent: MAHLIFE, TECHM) the old
     code was structurally unable to represent. Surfaced as a new,
     purely informational `t2_before_t1` field — it does not change
     `stage` or eligibility in Patch A.

  3. Trading-bar freshness — `t1_cross_age` / `t2_cross_age` now count
     completed trading bars since the cross (0 = crossed on the latest
     bar), replacing calendar-day subtraction. This matches both the
     module's own documented "30 trading days" intent and the bar-based
     convention already used by sma_rising().

Signal computation is factored into compute_signals(df) so the core
logic can be unit-tested against synthetic DataFrames without any
network/data-fetch dependency. analyze_stock() is unchanged in shape —
it fetches data, then delegates.
----------------------------------------------------------------------
"""

import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np
import pandas as pd
# yfinance is imported lazily inside analyze_stock() so that
# compute_signals() — the testable core logic — has no network/data-fetch
# dependency at all.

# ─────────────────────────────────────────────
# PARAMETERS
# ─────────────────────────────────────────────
DATA_PERIOD = "2y"
CROSS_LOOKBACK = 30          # trading bars (Patch A fix #3 — was calendar days)
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
# CROSSOVER EVENT DETECTION  (Patch A fix #2: reusable, unconditional)
# ─────────────────────────────────────────────
def detect_upward_crosses(fast, slow):
    """
    Return the index labels where `fast` crosses above `slow`
    (sign of the spread flips from negative to positive).

    Unconditional — finds every such event across the whole series
    regardless of the CURRENT relationship between fast and slow. This is
    what makes whipsaw detection possible: a stock can show a past 200/350
    upward cross here even if 200 is currently back below 350.
    """
    spread = fast - slow
    sign = np.sign(spread)
    changes = sign.diff().fillna(0)
    events = changes[changes == 2]
    return events.index


def bar_age(df, event_date):
    """
    Trading-bar age of an event (Patch A fix #3): 0 = event on the latest
    bar, 1 = one completed bar ago, etc. Deterministic — no calendar-day
    ambiguity from weekends/holidays.
    """
    cross_idx = df.index.get_loc(event_date)
    return len(df) - 1 - cross_idx


# ─────────────────────────────────────────────
# SIGNAL COMPUTATION  (testable without network)
# ─────────────────────────────────────────────
def compute_signals(df, symbol="TEST"):
    """
    Takes a DataFrame that already has Close, SMA_50, SMA_200, SMA_350
    columns (NaN rows already dropped) and returns (result, reason),
    matching the original analyze_stock() return shape.
    """
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
        return None, "not_qualified"

    if gc_200_350:
        # Fully stacked — check if qualifies for Stage 2
        if r50 and r200:
            stage = "Stage 2"
            stage_label = "🟢 STAGE 2 — Full position (100%)"
        else:
            stage = "Hold"
            stage_label = "🟢 HOLD BOTH — stacked but SMAs not all rising"
    else:
        # 200 < 350 — check if qualifies for Stage 1 (Patch A fix #1: Strict)
        if r50 and r200:
            stage = "Stage 1"
            stage_label = "🟡 STAGE 1 — Half position (50%)"
        else:
            stage = "Wait"
            stage_label = "⚪ WAIT — 50 and/or 200 SMA not rising"

    # ── T1 cross events (50/200) — unconditional, as before ─
    t1_events = detect_upward_crosses(df['SMA_50'], df['SMA_200'])
    t1_cross_date = None
    t1_cross_age = None
    t1_fresh = False
    last_t1 = None
    if len(t1_events) > 0:
        last_t1 = t1_events[-1]
        t1_cross_age = bar_age(df, last_t1)                     # fix #3
        t1_cross_date = last_t1.strftime("%Y-%m-%d")
        t1_fresh = t1_cross_age <= CROSS_LOOKBACK

    # ── T2 cross events (200/350) — now unconditional (fix #2) ─
    t2_events = detect_upward_crosses(df['SMA_200'], df['SMA_350'])
    t2_cross_date = None
    t2_cross_age = None
    t2_fresh = False
    last_t2 = None
    if len(t2_events) > 0:
        last_t2 = t2_events[-1]
        t2_cross_age = bar_age(df, last_t2)                     # fix #3
        t2_cross_date = last_t2.strftime("%Y-%m-%d")
        t2_fresh = t2_cross_age <= CROSS_LOOKBACK

    # Informational whipsaw flag (Patch A) — does NOT gate stage/eligibility.
    # Patch B decides how this feeds the T1_WHIPSAW state and whether a
    # t1_whipsaw_type (BROKEN_STACK / FAST_RECROSS) diagnostic is added.
    t2_before_t1 = bool(last_t1 is not None and last_t2 is not None and last_t2 < last_t1)

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

    result = {
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
        "t2_before_t1": t2_before_t1,     # NEW (Patch A) — informational only
    }
    return result, "ok"


# ─────────────────────────────────────────────
# STOCK ANALYSIS
# ─────────────────────────────────────────────
def analyze_stock(symbol):
    """
    Returns (result, reason).
    result is a dict on success, None otherwise.
    reason is "ok" on success, or one of:
        "no_data", "insufficient_history", "not_qualified",
        "exception: <ExceptionType>: <message>"
    """
    try:
        import yfinance as yf
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

        return compute_signals(df, symbol=symbol)

    except Exception as e:
        return None, f"exception: {type(e).__name__}: {e}"


# ─────────────────────────────────────────────
# SCANNER  (unchanged from original)
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
    skip_counts = {
        "no_data": 0,
        "insufficient_history": 0,
        "not_qualified": 0,
        "exception": 0,
    }
    skip_details = []  # symbol-level detail, only for true exceptions

    total = len(symbols)
    print(f"\n{'='*60}")
    print(f"  TWO-STAGE GOLDEN CROSS SCANNER")
    print(f"  Stage 1: Price > 50↑ > 200↑, 200 < 350 (50%)")
    print(f"  Stage 2: Price > 50↑ > 200↑ > 350 (100%)")
    print(f"  Scanning {total} stocks")
    print(f"  {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    print(f"{'='*60}\n")

    for idx, symbol in enumerate(symbols, 1):
        print(f"  [{idx}/{total}] {symbol}...", end='\r')
        result, reason = analyze_stock(symbol)

        if result:
            results.append(result)
        elif reason.startswith("exception"):
            skip_counts["exception"] += 1
            skip_details.append({
                "symbol": symbol.replace(".NS", ""),
                "reason": reason,
            })
            print(f"  ✗ {symbol}: {reason}")
        else:
            skip_counts[reason] += 1

    s1 = [r for r in results if r["stage"] == "Stage 1"]
    s2 = [r for r in results if r["stage"] == "Stage 2"]
    hold = [r for r in results if r["stage"] == "Hold"]
    wait = [r for r in results if r["stage"] == "Wait"]

    print(f"\n\n  ✓ Scan complete.")
    print(f"  Stage 2: {len(s2)} | Stage 1: {len(s1)} | Hold: {len(hold)} | Wait: {len(wait)}")
    print(f"  Not qualified (no setup): {skip_counts['not_qualified']}")
    print(f"  Insufficient history: {skip_counts['insufficient_history']}")
    print(f"  No data: {skip_counts['no_data']}")
    print(f"  Exceptions: {skip_counts['exception']}\n")

    return results, skip_counts, skip_details


# ─────────────────────────────────────────────
# OUTPUT  (unchanged from original)
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


def generate_markdown(results, total_scanned, skip_counts, skip_details):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    s1 = [r for r in results if r["stage"] == "Stage 1"]
    s2 = [r for r in results if r["stage"] == "Stage 2"]
    hold = [r for r in results if r["stage"] == "Hold"]
    wait = [r for r in results if r["stage"] == "Wait"]

    fresh_t1 = [r for r in results if r["t1_fresh"] and r["stage"] == "Stage 1"]
    fresh_t2 = [r for r in results if r["t2_fresh"] and r["stage"] == "Stage 2"]

    # Sort fresh entries by cross age — latest (smallest age) first
    fresh_t1.sort(key=lambda r: r["t1_cross_age"] if r["t1_cross_age"] is not None else 9999)
    fresh_t2.sort(key=lambda r: r["t2_cross_age"] if r["t2_cross_age"] is not None else 9999)

    s1.sort(key=lambda r: (0 if r["t1_fresh"] else 1, r["t1_cross_age"] or 9999))
    s2.sort(key=lambda r: (0 if r["t2_fresh"] else 1, r["t2_cross_age"] or 9999))

    total_skipped = sum(skip_counts.values())

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
        f"**Skipped:** {total_skipped}",
        "",
        f"**Skip breakdown:** "
        f"Not qualified: {skip_counts['not_qualified']} · "
        f"Insufficient history: {skip_counts['insufficient_history']} · "
        f"No data: {skip_counts['no_data']} · "
        f"Exceptions: {skip_counts['exception']}",
        "",
        "↑ = SMA rising (50: 5 bars, 200/350: 20 bars) · ↓ = SMA falling",
        "",
        "---",
        "",
    ]

    # ── Fresh entries ───────────────────────────────────────
    if fresh_t1 or fresh_t2:
        lines.append(f"## 🆕 Fresh Entries (last {CROSS_LOOKBACK} trading bars)")
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
    lines.append("## 🟡 Stage 1 — Half Position (Price > 50↑ > 200↑, 200 < 350)")
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

    # ── Wait (cross active but 50/200 not rising) ───────────
    if wait:
        lines.append("## ⚪ Wait — Cross active but 50 and/or 200 SMA not rising")
        lines.append("")
        lines.append("| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |")
        lines.append("|--------|-----|--------|---------|---------|----------|--------|------------|-------------|")
        for r in wait:
            lines.append(_table_row(r, show_t2=False))
        lines.append("")

    # ── Skipped / exceptions detail ─────────────────────────
    if skip_details:
        lines.append("## ⚠️ Exceptions (true script/API errors)")
        lines.append("")
        lines.append("| Symbol | Reason |")
        lines.append("|--------|--------|")
        for d in skip_details:
            lines.append(f"| {d['symbol']} | {d['reason']} |")
        lines.append("")

    # ── Legend ───────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>System Rules</summary>")
    lines.append("")
    lines.append("| Status | Condition | Action | Position |")
    lines.append("|--------|-----------|--------|----------|")
    lines.append("| 🆕 Fresh T1 | 50/200 bullish cross ≤30 trading bars | Candidate for T1 | — |")
    lines.append("| 🟡 Stage 1 | Price > 50 > 200, 200 < 350, 50↑ 200↑ | Buy T1 | 50% |")
    lines.append("| 🆕 Fresh T2 | 200/350 bullish cross ≤30 trading bars | Candidate for T2 | — |")
    lines.append("| 🟢 Stage 2 | Price > 50 > 200 > 350, 50↑ 200↑ | Add T2 | 100% |")
    lines.append("| ⚪ Wait | Cross active but SMA not rising | No action | — |")
    lines.append("")
    lines.append("**SMA Direction:** 50 SMA vs 5 trading bars ago · 200/350 SMA vs 20 trading bars ago")
    lines.append("")
    lines.append("**Skip reasons:**")
    lines.append("| Reason | Meaning |")
    lines.append("|--------|---------|")
    lines.append("| not_qualified | Real data, just not in a Price>50>200 setup right now (expected/normal) |")
    lines.append("| insufficient_history | Fewer than 360 bars or 21 clean SMA rows — too-new listing or data gap |")
    lines.append("| no_data | yfinance returned nothing for this symbol |")
    lines.append("| exception | Genuine script/API failure — worth investigating |")
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
# MAIN  (unchanged from original)
# ─────────────────────────────────────────────
if __name__ == '__main__':
    stock_list = Path(__file__).parent / "nifty500.txt"
    symbols = load_stock_list(stock_list)

    results, skip_counts, skip_details = run_scan(symbols)

    out_dir = Path(__file__).parent
    md = generate_markdown(results, len(symbols), skip_counts, skip_details)
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
        "skipped": {
            "not_qualified": skip_counts["not_qualified"],
            "insufficient_history": skip_counts["insufficient_history"],
            "no_data": skip_counts["no_data"],
            "exception": skip_counts["exception"],
        },
        "exception_details": skip_details,
        "stocks": results,
    }

    (out_dir / "crossovers.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"  Wrote crossovers.json")

    # Copy JSON to docs/ for GitHub Pages
    docs_dir = out_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "crossovers.json").write_text(json.dumps(j, indent=2, default=str))
    print(f"  Wrote docs/crossovers.json")
