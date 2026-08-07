# Golden Cross Monitor

Automated daily check of 100/350 SMA golden cross health for Indian equities.  
Based on the **Turtle SMA Crossover v2.0** system.

## What it checks

For each stock in `watchlist.txt`:

| Check | Condition | Signal |
|-------|-----------|--------|
| 🟢 HEALTHY | Golden cross intact, price > 100 SMA | Hold |
| 🟡 CAUTION | Price < 100 SMA but RSI > 50 | Watch closely |
| 🟡 EXTENDED | Price >15% above 100 SMA | No new entry |
| 🟠 REDUCE | Price < 100 SMA AND RSI < 50 | Rule 2.1 — reduce 50% |
| 🔴 DEATH CROSS | 100 SMA < 350 SMA | Rule 2.2 — full exit |

Also checks **Nifty 500** market health (S4 from the Turtle system).

## Weekly Nifty 500 Crossover Scan

Scans all 500 stocks in `nifty500.txt` every Saturday for active golden crosses.
Highlights **fresh crosses** (within the last 30 trading days) separately so you can
spot new candidates for fundamental screening.

Output: [`crossovers.md`](crossovers.md)

## Setup

1. Fork or clone this repo
2. Add your stocks to `watchlist.txt` (one per line, with `.NS` suffix)
3. Populate `nifty500.txt` with Nifty 500 symbols (download from [NSE](https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv))
4. Push to GitHub — Actions run automatically:
   - **Daily** (Mon–Fri 16:30 IST): watchlist health → `status.md`
   - **Weekly** (Saturday 06:00 IST): Nifty 500 crossover scan → `crossovers.md`
5. Monitor the `.md` files for results

### Manual trigger

Go to **Actions** → pick the workflow → **Run workflow**

## Files

| File | Purpose |
|------|---------|
| `watchlist.txt` | Your watchlist stocks (edit this) |
| `nifty500.txt` | Nifty 500 universe for crossover scanning (edit this) |
| `scanner.py` | Daily watchlist health check |
| `crossover_scan.py` | Weekly Nifty 500 golden crossover scanner |
| `status.md` | Watchlist results (auto-updated daily) |
| `status.json` | Watchlist results — machine-readable |
| `crossovers.md` | Nifty 500 crossover results (auto-updated weekly) |
| `crossovers.json` | Crossover results — machine-readable |

## Local run

```bash
pip install -r requirements.txt

# Daily watchlist check
python scanner.py        # → status.md

# Weekly Nifty 500 scan
python crossover_scan.py # → crossovers.md
```
