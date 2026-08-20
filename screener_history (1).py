#!/usr/bin/env python3
"""
Fetch Screener.in historical Price, DMA50, DMA200, PE, EPS and Median PE.

Output:
    screener_data/AVANTEL.json
    screener_data/TCS.json
    ...

The Screener chart API is:
    /api/company/{company_id}/chart/

The metric names below are the same ones used by Screener's
Price and PE chart buttons.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import requests


BASE_URL = "https://www.screener.in/api/company/{company_id}/chart/"

# Screener's Price chart uses:
# Price-DMA50-DMA200-Volume
#
# We omit Volume because it wasn't requested.
METRICS = [
    "Price",
    "DMA50",
    "DMA200",
    "Price to Earning",
    "Median PE",
    "EPS",
]


def build_url(company_id: int, days: int) -> str:
    params = {
        "q": "-".join(METRICS),
        "days": days,
        "consolidated": "true",
    }
    return (
        BASE_URL.format(company_id=company_id)
        + "?"
        + urlencode(params)
    )


def latest_valid(values):
    """Return the latest [date, value, ...] whose value isn't null."""
    valid = [
        row for row in values
        if len(row) >= 2 and row[1] is not None
    ]
    return valid[-1] if valid else None


def fetch_company(session, symbol, company_id, days=1825, timeout=30):
    url = build_url(company_id, days)

    # Screener's own URLs don't use the .NS suffix (that's a
    # Yahoo/yfinance convention) — strip it just for the Referer,
    # while keeping the .NS symbol everywhere else (filenames, JSON,
    # companies.json keys) so it stays consistent with the rest of
    # the repo's naming.
    screener_symbol = symbol[:-3] if symbol.endswith(".NS") else symbol

    headers = {
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": (
            f"https://www.screener.in/company/"
            f"{screener_symbol}/consolidated/"
        ),
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
    }

    response = session.get(
        url,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    payload = response.json()

    if "datasets" not in payload:
        raise ValueError(
            f"Unexpected response for {symbol}: "
            f"{list(payload.keys())}"
        )

    # Convert Screener's dataset list into a predictable structure.
    datasets = {
        item["metric"]: item
        for item in payload["datasets"]
        if item.get("metric")
    }

    data = {
        "price": datasets.get("Price", {}),
        "dma50": datasets.get("DMA50", {}),
        "dma200": datasets.get("DMA200", {}),
        "pe": datasets.get("Price to Earning", {}),
        "eps": datasets.get("EPS", {}),
        "median_pe": datasets.get("Median PE", {}),
    }

    latest_price = latest_valid(data["price"].get("values", []))
    latest_dma50 = latest_valid(data["dma50"].get("values", []))
    latest_dma200 = latest_valid(data["dma200"].get("values", []))
    latest_pe = latest_valid(data["pe"].get("values", []))
    latest_eps = latest_valid(data["eps"].get("values", []))

    median_values = data["median_pe"].get("values", [])
    median_pe = (
        median_values[-1][1]
        if median_values
        else None
    )

    pe_to_median = None
    if latest_pe and median_pe not in (None, 0):
        pe_to_median = round(
            float(latest_pe[1]) / float(median_pe),
            4,
        )

    return {
        "source": "Screener.in",
        "symbol": symbol,
        "company_id": company_id,
        "consolidated": True,
        "days": days,
        "api_url": url,

        "data": {
            "price": data["price"],
            "dma50": data["dma50"],
            "dma200": data["dma200"],
            "pe": data["pe"],
            "eps": data["eps"],
            "median_pe": data["median_pe"],
        },

        "latest": {
            "price": latest_price,
            "dma50": latest_dma50,
            "dma200": latest_dma200,
            "pe": latest_pe,
            "eps": latest_eps,
            "median_pe": median_pe,
            "pe_to_median": pe_to_median,
        },
    }


def parse_company(value):
    """
    Parse SYMBOL=COMPANY_ID.

    Example:
        AVANTEL=340
    """
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            f"Use SYMBOL=COMPANY_ID, e.g. AVANTEL=340"
        )

    symbol, company_id = value.split("=", 1)

    symbol = symbol.strip().upper()

    try:
        company_id = int(company_id.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid company ID: {company_id}"
        )

    return symbol, company_id


def load_companies(path):
    """
    Load:
        {
            "AVANTEL": 340,
            "TCS": 66
        }
    """
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    if not isinstance(obj, dict):
        raise ValueError(
            "companies.json must contain an object: "
            '{"AVANTEL": 340, "TCS": 66}'
        )

    return [
        (str(symbol).upper(), int(company_id))
        for symbol, company_id in obj.items()
    ]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Screener Price/DMA/PE/EPS history "
            "into one JSON file per company."
        )
    )

    parser.add_argument(
        "--company",
        action="append",
        type=parse_company,
        help=(
            "SYMBOL=COMPANY_ID. Repeat for multiple companies. "
            "Example: --company AVANTEL=340"
        ),
    )

    parser.add_argument(
        "--companies",
        type=Path,
        help=(
            "JSON file containing "
            '{"AVANTEL": 340, "TCS": 66}'
        ),
    )

    parser.add_argument(
        "--days",
        type=int,
        default=1825,
        choices=[365, 1095, 1825, 3652, 10000],
        help=(
            "History: 365=1Y, 1095=3Y, 1825=5Y, "
            "3652=10Y, 10000=Max. Default: 1825."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("screener_data"),
        help="Output directory. Default: screener_data/",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between companies. Default: 1 second.",
    )

    args = parser.parse_args()

    companies = []

    if args.company:
        companies.extend(args.company)

    if args.companies:
        companies.extend(load_companies(args.companies))

    if not companies:
        parser.error(
            "Provide --company SYMBOL=ID or --companies companies.json"
        )

    # De-duplicate symbols.
    unique = {}
    for symbol, company_id in companies:
        unique[symbol] = company_id

    companies = list(unique.items())

    args.output.mkdir(
        parents=True,
        exist_ok=True,
    )

    session = requests.Session()

    for index, (symbol, company_id) in enumerate(
        companies,
        start=1,
    ):
        print(
            f"[{index}/{len(companies)}] "
            f"{symbol} (company_id={company_id})"
        )

        try:
            result = fetch_company(
                session=session,
                symbol=symbol,
                company_id=company_id,
                days=args.days,
            )

            output_file = (
                args.output / f"{symbol}.json"
            )

            with output_file.open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    result,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            latest = result["latest"]

            print(f"  Saved: {output_file}")
            print(f"  PE:       {latest['pe']}")
            print(f"  EPS:      {latest['eps']}")
            print(f"  Price:    {latest['price']}")
            print(f"  DMA50:    {latest['dma50']}")
            print(f"  DMA200:   {latest['dma200']}")
            print(f"  Median PE: {latest['median_pe']}")
            print(f"  PE/Median: {latest['pe_to_median']}")

        except requests.HTTPError as exc:
            print(
                f"  HTTP ERROR: {exc}",
                file=sys.stderr,
            )

        except Exception as exc:
            print(
                f"  ERROR: {exc}",
                file=sys.stderr,
            )

        if index < len(companies):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
