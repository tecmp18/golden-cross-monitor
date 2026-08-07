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

## Setup

1. Fork or clone this repo
2. Add your stocks to `watchlist.txt` (one per line, with `.NS` suffix)
3. Push to GitHub — the Action runs Mon–Fri at 16:30 IST automatically
4. Monitor [`status.md`](status.md) for daily results

### Manual trigger

Go to **Actions** → **Daily Golden Cross Scan** → **Run workflow**

## Files

| File | Purpose |
|------|---------|
| `watchlist.txt` | Your stocks (edit this) |
| `scanner.py` | The scan logic |
| `status.md` | Human-readable results (auto-updated) |
| `status.json` | Machine-readable results (auto-updated) |

## Local run

```bash
pip install -r requirements.txt
python scanner.py
# Check status.md
```
