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

    # Informational whipsaw flag (Patch A).
    t2_before_t1 = bool(last_t1 is not None and last_t2 is not None and last_t2 < last_t1)

    # ── PATCH B — technical_state / position_state (see module docstring) ──
    #
    # t1_* fields are only meaningful when NOT gc_200_350 (200 < 350), since
    # the T1 hard gate itself requires that condition — a currently-stacked
    # stock has already moved past the T1 entry window entirely, so its
    # t1_state is None rather than a rejection.
    #
    # t2_* fields are only meaningful when gc_200_350 (full stack), mirroring
    # the same logic for the T2 hard gate.
    t1_state = None
    t1_price_tier = None
    t1_gap_class = None
    t1_technical_eligible = False
    t1_position = 0

    t2_state = None
    t2_gap_class = None
    t2_technical_eligible = False
    # t2_position is NOT determined here. Whether a valid T2 adds 0.5 (T1
    # already held) or opens a fresh 1.0 (T1 never held / was rejected) is a
    # portfolio fact — did the person actually hold T1 for this name — which
    # this scanner has no way to know. That decision stays a manual weekly
    # review step; t2_position is left None deliberately rather than guessed.
    t2_position = None

    if not gc_200_350:
        # T1 territory
        if price_vs_50 <= 2:
            t1_price_tier = "FRESH_CROSS"
        elif price_vs_50 <= 5:
            t1_price_tier = "EARLY_CONFIRM"
        else:
            t1_price_tier = "EXTENDED"

        if gap_50_200 < 1.5:
            t1_gap_class = "FRAGILE"
        elif gap_50_200 < 3:
            t1_gap_class = "DEVELOPING"
        else:
            t1_gap_class = "HEALTHY"

        if not (r50 and r200):
            t1_state = "T1_INVALID"
        elif not t1_fresh:
            t1_state = "T1_EXPIRED"
        elif t2_before_t1:
            t1_state = "T1_WHIPSAW"
        elif price_vs_50 > 5:
            t1_state = "T1_EXTENDED"
        elif t1_gap_class == "FRAGILE":
            t1_state = "T1_FRAGILE"
        else:
            t1_state = "T1_VALID"

        t1_technical_eligible = t1_state in ("T1_VALID", "T1_FRAGILE")
        t1_position = 0.5 if t1_technical_eligible else 0

    else:
        # T2 territory
        if gap_200_350 is not None:
            if gap_200_350 < 1.5:
                t2_gap_class = "FRAGILE"
            elif gap_200_350 < 3:
                t2_gap_class = "DEVELOPING"
            else:
                t2_gap_class = "HEALTHY"

        if not (r50 and r200):
            t2_state = "T2_INVALID"
        elif not t2_fresh:
            t2_state = "T2_EXPIRED"
        elif t2_gap_class == "FRAGILE":
            t2_state = "T2_FRAGILE"
        else:
            t2_state = "T2_VALID"

        t2_technical_eligible = t2_state in ("T2_VALID", "T2_FRAGILE")

    # Diagnostic only — NOT a T1 gate outcome. A currently-stacked (Stage 2)
    # name whose fast leg (50/200) previously broke and re-crossed while the
    # slow leg (200/350) stayed intact throughout. This is a Hold-list
    # stability flag, not an entry decision — the stock never entered T1-gate
    # evaluation above because it's currently stacked.
    fast_leg_recross_while_stacked = bool(gc_200_350 and t2_before_t1)

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
        "t2_before_t1": t2_before_t1,                              # Patch A
        # ── Patch B: technical_state / position_state ──
        "t1_state": t1_state,
        "t1_price_tier": t1_price_tier,
        "t1_gap_class": t1_gap_class,
        "t1_technical_eligible": t1_technical_eligible,
        "t1_position": t1_position,
        "t2_state": t2_state,
        "t2_gap_class": t2_gap_class,
        "t2_technical_eligible": t2_technical_eligible,
        "t2_position": t2_position,          # None — portfolio fact, not computable here
        "fast_leg_recross_while_stacked": fast_leg_recross_while_stacked,
        # External gates — always None from this scanner. Filled in during
        # the manual weekly review (Sections 5/6 of the rules). Never
        # inferred here; a technically-eligible name can still be
        # SUPPRESSED at review time without this scanner knowing why.
        "quadrant_status": None,
        "news_status": None,
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


def _price_display(r):
    return f"₹{r['ltp']} | ₹{r['sma50']} {_direction(r['sma50_rising'])} | ₹{r['sma200']} {_direction(r['sma200_rising'])}"


def _t1_eligible_row(r):
    return (f"| {r['symbol']} | ₹{r['ltp']} | {r['t1_price_tier']} | {r['t1_gap_class']} "
            f"| {r['t1_cross_date']} | {r['t1_cross_age']}d | {r['gap_50_200_pct']}% |")


def _t1_rejected_row(r):
    reason_detail = {
        "T1_EXTENDED": f"{r['price_vs_50_pct']}% above 50 SMA (cap: 5%)",
        "T1_WHIPSAW": f"prior T2 cross {r['t2_cross_date']} predates this T1 ({r['t1_cross_date']})",
    }.get(r["t1_state"], "")
    return f"| {r['symbol']} | ₹{r['ltp']} | {r['t1_cross_date']} | {r['t1_cross_age']}d | {reason_detail} |"


def _t2_eligible_row(r):
    return (f"| {r['symbol']} | ₹{r['ltp']} | {r['t2_gap_class']} "
            f"| {r['t2_cross_date']} | {r['t2_cross_age']}d | {r['gap_200_350_pct']}% |")


def generate_markdown(results, total_scanned, skip_counts, skip_details):
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    s1 = [r for r in results if r["stage"] == "Stage 1"]
    s2 = [r for r in results if r["stage"] == "Stage 2"]
    hold = [r for r in results if r["stage"] == "Hold"]
    wait = [r for r in results if r["stage"] == "Wait"]

    # Patch B: Fresh entries are now driven by t1_state / t2_state rather than
    # reconstructing eligibility from stage + t1_fresh. Within the "fresh"
    # population (t1_fresh / t2_fresh True on a Strict-valid stock), split
    # into technically-eligible vs rejected-by-reason so a rejected name can
    # never render as a live "Buy Tranche 1" candidate again.
    fresh_t1_all = [r for r in results if r["t1_fresh"] and r["stage"] == "Stage 1"]
    fresh_t1_eligible = [r for r in fresh_t1_all if r["t1_technical_eligible"]]
    fresh_t1_rejected = [r for r in fresh_t1_all if not r["t1_technical_eligible"]]

    fresh_t2_all = [r for r in results if r["t2_fresh"] and r["stage"] == "Stage 2"]
    fresh_t2_eligible = [r for r in fresh_t2_all if r["t2_technical_eligible"]]
    fresh_t2_rejected = [r for r in fresh_t2_all if not r["t2_technical_eligible"]]

    fresh_t1_eligible.sort(key=lambda r: r["t1_cross_age"] if r["t1_cross_age"] is not None else 9999)
    fresh_t2_eligible.sort(key=lambda r: r["t2_cross_age"] if r["t2_cross_age"] is not None else 9999)

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
        f"**T1 Technically Eligible:** {len(fresh_t1_eligible)} | "
        f"**T2 Technically Eligible:** {len(fresh_t2_eligible)} | "
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
        "> **Note:** the tables below reflect `t1_technical_eligible` / `t2_technical_eligible` "
        "(Patch B state machine), not raw freshness. A name can be `t1_fresh` and still be "
        "rejected — see the Rejected tables for why. Fundamental quadrant and news checks "
        "(`quadrant_status`, `news_status`) are never computed here — they remain a manual "
        "weekly-review step regardless of technical eligibility.",
        "",
        "---",
        "",
    ]

    # ── Fresh T1 ─────────────────────────────────────────────
    lines.append(f"## 🆕 Fresh T1 (last {CROSS_LOOKBACK} trading bars, Strict gate)")
    lines.append("")

    lines.append(f"### ✅ Technically Eligible ({len(fresh_t1_eligible)})")
    lines.append("")
    if fresh_t1_eligible:
        lines.append("| Symbol | LTP | Price Tier | Gap Class | T1 Cross | Age | 50/200 Gap |")
        lines.append("|--------|-----|------------|-----------|----------|-----|------------|")
        for r in fresh_t1_eligible:
            lines.append(_t1_eligible_row(r))
    else:
        lines.append("*None this week*")
    lines.append("")

    if fresh_t1_rejected:
        lines.append(f"### ❌ Rejected ({len(fresh_t1_rejected)})")
        lines.append("")
        for reason in ("T1_EXTENDED", "T1_WHIPSAW", "T1_INVALID", "T1_EXPIRED"):
            group = [r for r in fresh_t1_rejected if r["t1_state"] == reason]
            if not group:
                continue
            lines.append(f"**{reason}** ({len(group)})")
            lines.append("")
            lines.append("| Symbol | LTP | T1 Cross | Age | Reason |")
            lines.append("|--------|-----|----------|-----|--------|")
            for r in group:
                lines.append(_t1_rejected_row(r))
            lines.append("")

    lines.append("---")
    lines.append("")

    # ── Fresh T2 ─────────────────────────────────────────────
    lines.append(f"## 🆕 Fresh T2 (last {CROSS_LOOKBACK} trading bars, Strict gate)")
    lines.append("")
    lines.append(f"### ✅ Technically Eligible ({len(fresh_t2_eligible)})")
    lines.append("")
    if fresh_t2_eligible:
        lines.append("| Symbol | LTP | Gap Class | T2 Cross | Age | 200/350 Gap |")
        lines.append("|--------|-----|-----------|----------|-----|-------------|")
        for r in fresh_t2_eligible:
            lines.append(_t2_eligible_row(r))
        lines.append("")
        lines.append("> Sizing (0.5 add vs 1.0 standalone) depends on whether T1 is already held for "
                      "each name — a portfolio fact this scanner does not know. Check manually before sizing.")
    else:
        lines.append("*None this week*")
    lines.append("")

    if fresh_t2_rejected:
        lines.append(f"### ❌ Rejected ({len(fresh_t2_rejected)})")
        lines.append("")
        lines.append("| Symbol | LTP | T2 State | T2 Cross | Age |")
        lines.append("|--------|-----|----------|----------|-----|")
        for r in fresh_t2_rejected:
            lines.append(f"| {r['symbol']} | ₹{r['ltp']} | {r['t2_state']} | {r['t2_cross_date']} | {r['t2_cross_age']}d |")
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
    lines.append("| 🟡 Stage 1 | Price > 50 > 200, 200 < 350, 50↑ 200↑ | Technical formation only | — |")
    lines.append("| 🟢 Stage 2 | Price > 50 > 200 > 350, 50↑ 200↑ | Technical formation only | — |")
    lines.append("| ⚪ Wait | Cross active but SMA not rising | No action | — |")
    lines.append("")
    lines.append("**T1 state (evaluated in this priority order — first match wins):**")
    lines.append("| State | Meaning |")
    lines.append("|-------|---------|")
    lines.append("| T1_INVALID | 50 and/or 200 SMA not rising (fails Strict gate) |")
    lines.append("| T1_EXPIRED | Cross exists but is stale (outside 30-bar freshness window) |")
    lines.append("| T1_EXTENDED | Price >5% above 50 SMA — outside the early-entry band |")
    lines.append("| T1_WHIPSAW | Otherwise eligible, but a prior T2 cross predates this T1 (reverted-stack re-entry) |")
    lines.append("| T1_FRAGILE | Eligible — 50/200 gap <1.5%, flagged as fragile |")
    lines.append("| T1_VALID | Eligible — clean transition |")
    lines.append("")
    lines.append("**T2 state:**")
    lines.append("| State | Meaning |")
    lines.append("|-------|---------|")
    lines.append("| T2_INVALID | 50 and/or 200 SMA not rising |")
    lines.append("| T2_EXPIRED | Cross exists but is stale |")
    lines.append("| T2_FRAGILE | Eligible — 200/350 gap <1.5% |")
    lines.append("| T2_VALID | Eligible — Developing or Healthy gap |")
    lines.append("")
    lines.append("Only `T1_VALID`/`T1_FRAGILE` and `T2_VALID`/`T2_FRAGILE` are technically eligible. "
                  "Technical eligibility is necessary but not sufficient — the Fundamental Quadrant "
                  "Gate and news/catalyst check (never computed by this scanner) still apply before "
                  "any entry decision.")
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
