#!/usr/bin/env python3
"""
Nifty 500 — Two-Stage Golden Cross Scanner (Patch A — correctness fixes)
=========================================================================

This is crossover_scan.py with three targeted fixes, and nothing else changed:

  1. T1 Strict gate — Stage 1 now requires BOTH r50 and r200 rising,
     matching the production rule in Technical Tranche Rules v2.0.
     (Previously only r50 was checked; r200 was computed but unused.)

  2. Whipsaw-capable T2 detection — the 200/350 crossover-event scan now
     runs unconditionally over the full lookback window, independent of
     whether the stock is CURRENTLY stacked 200>350. Previously it only
     ran `if gc_200_350`, which made it structurally impossible to see a
     T2 event that later reverted — exactly the MAHLIFE/TECHM pattern.
     A new `t2_before_t1` field surfaces this; it does not (yet) change
     `stage` — that's a Patch B policy decision, not a Patch A correctness
     fix.

  3. Trading-bar freshness — `t1_cross_age` / `t2_cross_age` now count
     completed trading bars since the cross (0 = crossed on the latest
     bar), not calendar days. This matches the module's own documented
     "30 trading days" intent and the bar-based convention already used
     by sma_rising().

Signal computation is factored into compute_signals(df) so it can be
tested against synthetic DataFrames without hitting yfinance/network.
analyze_stock() is unchanged in shape — it fetches data, then delegates.
"""

import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np
import pandas as pd
# yfinance is imported lazily inside analyze_stock() so that compute_signals()
# — the testable core logic — has no network/data-fetch dependency at all.

# ─────────────────────────────────────────────
# PARAMETERS
# ─────────────────────────────────────────────
DATA_PERIOD = "2y"
CROSS_LOOKBACK = 30          # trading bars, not calendar days (fix #3)
IST = ZoneInfo("Asia/Kolkata")


# ─────────────────────────────────────────────
# SMA DIRECTION  (unchanged)
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
# CROSSOVER EVENT DETECTION  (fix #2: reusable, unconditional)
# ─────────────────────────────────────────────
def detect_upward_crosses(fast, slow):
    """
    Return the index labels where `fast` crosses above `slow`
    (sign of the spread flips from negative to positive).

    This is unconditional — it finds every such event across the whole
    series regardless of the CURRENT relationship between fast and slow.
    That's what makes whipsaw detection possible: a stock can show a
    past 200/350 upward cross here even if 200 is currently back below
    350.
    """
    spread = fast - slow
    sign = np.sign(spread)
    changes = sign.diff().fillna(0)
    events = changes[changes == 2]
    return events.index


def bar_age(df, event_date):
    """
    Trading-bar age of an event (fix #3): 0 = event on the latest bar,
    1 = one completed bar ago, etc. Deterministic, no calendar-day
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
    columns (NaN rows already dropped) and returns the same result dict
    shape as before, plus:
        - t2_before_t1   (bool)  — informational whipsaw flag, Patch A
        - t1_cross_age / t2_cross_age now measured in trading bars
        - Stage 1 now gated on r50 AND r200 (Strict)
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

    # ── Stage classification (fix #1: Strict T1 gate) ───────
    if not (price_above_50 and gc_50_200):
        return None, "not_qualified"

    if gc_200_350:
        if r50 and r200:
            stage = "Stage 2"
            stage_label = "🟢 STAGE 2 — Full position (100%)"
        else:
            stage = "Hold"
            stage_label = "🟢 HOLD BOTH — stacked but SMAs not all rising"
    else:
        if r50 and r200:                                        # <-- FIX #1
            stage = "Stage 1"
            stage_label = "🟡 STAGE 1 — Half position (50%) [Strict: 50↑ & 200↑]"
        else:
            stage = "Wait"
            stage_label = "⚪ WAIT — 50 and/or 200 SMA not rising (Strict gate)"

    # ── T1 cross events (50/200) — always unconditional, unchanged ──
    t1_events = detect_upward_crosses(df['SMA_50'], df['SMA_200'])
    t1_cross_date = None
    t1_cross_age = None
    t1_fresh = False
    last_t1 = None
    if len(t1_events) > 0:
        last_t1 = t1_events[-1]
        t1_cross_age = bar_age(df, last_t1)                      # <-- FIX #3
        t1_cross_date = last_t1.strftime("%Y-%m-%d")
        t1_fresh = t1_cross_age <= CROSS_LOOKBACK

    # ── T2 cross events (200/350) — now unconditional (fix #2) ──────
    t2_events = detect_upward_crosses(df['SMA_200'], df['SMA_350'])
    t2_cross_date = None
    t2_cross_age = None
    t2_fresh = False
    last_t2 = None
    if len(t2_events) > 0:
        last_t2 = t2_events[-1]
        t2_cross_age = bar_age(df, last_t2)                      # <-- FIX #3
        t2_cross_date = last_t2.strftime("%Y-%m-%d")
        t2_fresh = t2_cross_age <= CROSS_LOOKBACK

    # ── Whipsaw flag (informational only — Patch A does not change
    #     `stage` based on this; that's a Patch B policy decision) ──
    t2_before_t1 = bool(last_t1 is not None and last_t2 is not None and last_t2 < last_t1)

    # Freshness label
    if stage == "Stage 2" and t2_fresh:
        freshness = "🆕 Fresh T2"
    elif stage == "Stage 1" and t1_fresh:
        freshness = "🆕 Fresh T1"
    else:
        freshness = "Established"

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
        "t2_before_t1": t2_before_t1,     # NEW — informational whipsaw flag
    }
    return result, "ok"


# ─────────────────────────────────────────────
# STOCK ANALYSIS  (unchanged except delegating to compute_signals)
# ─────────────────────────────────────────────
def analyze_stock(symbol):
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


# NOTE: run_scan(), generate_markdown(), and __main__ are unchanged from
# the original file and are omitted here for brevity in this patch preview.
# When applying: keep those sections as-is, and add "t2_before_t1" to any
# table row rendering you want it to appear in (optional for Patch A —
# it's informational, not required for the markdown output to function).
