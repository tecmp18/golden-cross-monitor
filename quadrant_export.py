#!/usr/bin/env python3
"""
Read every screener_data/{SYMBOL}.json (produced by screener_history.py)
and build a single CSV of EPS growth % and P/E change % per symbol, over
a configurable lookback window — ready to drop straight into
quadrant-scanner.html.

Usage:
    python quadrant_export.py --input screener_data --months 3

Output:
    watchlist_quadrant.csv
        Symbol, EPS Growth %, PE Change %, Latest EPS, Prior EPS,
        Latest PE, Prior PE, Latest Date, Prior Date (as-of)

Why "months" and not "days" for the lookback:
    EPS only updates on earnings dates (roughly quarterly), so a 1-month
    window will show 0% EPS growth for most stocks most months, unless
    the window happens to straddle a print. 3 months is a more honest
    default for spotting real EPS movement; use --months 1 if you
    specifically want a tight, most-recent-print-only comparison.
"""

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path


def parse_date(s):
    return date.fromisoformat(s)


def latest_on_or_before(values, target_date):
    """
    Given a list of [date_str, value] pairs (any ordering, may include
    None values), return the [date, value] entry with the latest date
    that is <= target_date. Returns None if no such entry exists.
    """
    candidates = [
        (parse_date(row[0]), row[1])
        for row in values
        if len(row) >= 2 and row[1] is not None
    ]
    candidates = [c for c in candidates if c[0] <= target_date]
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])


def latest_overall(values):
    candidates = [
        (parse_date(row[0]), row[1])
        for row in values
        if len(row) >= 2 and row[1] is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])


def latest_median_pe(values):
    """
    median_pe values come as [date_str, "41.3"] (string, not float) and
    Screener typically only stamps two points bracketing the window —
    just take whichever is latest and cast it to float.
    """
    row = latest_overall(values)
    if row is None:
        return None
    try:
        return float(row[1])
    except (TypeError, ValueError):
        return None


def months_ago(d, months):
    # Simple month subtraction without extra deps (dateutil not assumed).
    year = d.year
    month = d.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(d.day, 28)  # avoid day-overflow issues (Feb etc.)
    return date(year, month, day)


def pct_change(old, new):
    if old in (None, 0):
        return None
    return round(((float(new) - float(old)) / abs(float(old))) * 100, 2)


def process_symbol(path, months):
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    symbol = payload.get("symbol", path.stem)
    eps_values = payload.get("data", {}).get("eps", {}).get("values", [])
    pe_values = payload.get("data", {}).get("pe", {}).get("values", [])
    median_pe_values = payload.get("data", {}).get("median_pe", {}).get("values", [])

    latest_eps_row = latest_overall(eps_values)
    latest_pe_row = latest_overall(pe_values)

    if not latest_eps_row or not latest_pe_row:
        return None, f"{symbol}: missing EPS or PE data entirely"

    latest_date = max(latest_eps_row[0], latest_pe_row[0])
    target_date = months_ago(latest_date, months)

    prior_eps_row = latest_on_or_before(eps_values, target_date)
    prior_pe_row = latest_on_or_before(pe_values, target_date)

    if not prior_eps_row or not prior_pe_row:
        return None, (
            f"{symbol}: not enough history for a {months}-month lookback "
            f"(earliest data may be too recent)"
        )

    eps_growth = pct_change(prior_eps_row[1], latest_eps_row[1])
    pe_change = pct_change(prior_pe_row[1], latest_pe_row[1])

    if eps_growth is None or pe_change is None:
        return None, f"{symbol}: zero baseline value, can't compute % change"

    median_pe = latest_median_pe(median_pe_values)
    pe_to_median = None
    if median_pe not in (None, 0):
        pe_to_median = round(float(latest_pe_row[1]) / median_pe, 2)

    row = {
        "Symbol": symbol,
        "EPS Growth %": eps_growth,
        "PE Change %": pe_change,
        "PE / Median PE": pe_to_median,
        "Latest EPS": latest_eps_row[1],
        "Latest EPS Date": latest_eps_row[0].isoformat(),
        "Prior EPS": prior_eps_row[1],
        "Prior EPS Date": prior_eps_row[0].isoformat(),
        "Latest PE": latest_pe_row[1],
        "Latest PE Date": latest_pe_row[0].isoformat(),
        "Prior PE": prior_pe_row[1],
        "Prior PE Date": prior_pe_row[0].isoformat(),
        "Median PE": median_pe,
        "Lookback target (as-of)": target_date.isoformat(),
    }
    return row, None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a quadrant-ready CSV (EPS Growth %, PE Change %) "
            "from screener_history.py's per-symbol JSON output."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("screener_data"),
        help="Directory of per-symbol JSON files. Default: screener_data/",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("watchlist_quadrant.csv"),
        help="Output CSV path. Default: watchlist_quadrant.csv",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help=(
            "Lookback window in months for the growth/change comparison. "
            "Default: 3 (quarterly) — EPS is a step function, so short "
            "windows often show 0%% growth unless they straddle an "
            "earnings date."
        ),
    )
    args = parser.parse_args()

    if not args.input.is_dir():
        parser.error(f"Input directory not found: {args.input}")

    files = sorted(args.input.glob("*.json"))
    if not files:
        parser.error(f"No JSON files found in {args.input}")

    rows = []
    skipped = []

    for path in files:
        try:
            row, err = process_symbol(path, args.months)
        except Exception as exc:  # one bad file shouldn't kill the run
            row, err = None, f"{path.name}: unexpected error — {exc}"

        if row:
            rows.append(row)
        else:
            skipped.append(err)

    if not rows:
        print("No rows produced — nothing written.", file=sys.stderr)
        sys.exit(1)

    fieldnames = [
        "Symbol", "EPS Growth %", "PE Change %", "PE / Median PE",
        "Latest EPS", "Latest EPS Date", "Prior EPS", "Prior EPS Date",
        "Latest PE", "Latest PE Date", "Prior PE", "Prior PE Date",
        "Median PE", "Lookback target (as-of)",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")
    if skipped:
        print(f"\nSkipped {len(skipped)}:", file=sys.stderr)
        for msg in skipped:
            print(f"  - {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()
