# Golden Cross Monitor

Automated daily and weekly technical analysis of SMA crossover health for Indian equities.

Based on the **Technical Tranche Rules v2.0** system.

The system uses a two-stage SMA crossover structure:

* **T1 — Stage 1:** 50 SMA crosses above 200 SMA
* **T2 — Stage 2:** 200 SMA crosses above 350 SMA

T1 and T2 are evaluated independently and can progress a position from **0 → 0.5 → 1.0 tranche**. No averaging is used.

---

## What it checks

### Stage 1 — T1

A T1 formation requires:

* Price > 50 SMA > 200 SMA
* 200 SMA is rising
* 50 SMA has crossed above 200 SMA

Fresh T1 formations are evaluated using the **30-trading-bar freshness window**.

| T1 condition                           | State              | Technical eligibility |
| -------------------------------------- | ------------------ | --------------------- |
| Fresh/developing healthy 50/200 cross  | `T1_VALID`         | ✅ Yes                 |
| Fresh cross with <1.5% 50/200 gap      | `T1_FRAGILE`       | ✅ Yes, 0.5 tranche    |
| T2 occurred before this T1 cross       | `T1_WHIPSAW`       | ❌ No                  |
| Price >5% above 50 SMA                 | `T1_EXTENDED`      | ❌ No                  |
| 200 SMA not rising / formation invalid | `T1_INVALID`       | ❌ No                  |
| Cross older than 30 trading bars       | `T1_EXPIRED`       | ❌ No                  |
| Fundamental quadrant fails             | `T1_QUADRANT_FAIL` | ❌ Suppressed          |
| News/catalyst risk                     | `T1_NEWS_RISK`     | ❌ Suppressed          |
| Replaced by a later valid formation    | `T1_SUPERSEDED`    | ❌ No                  |

### T1 position

A technically eligible T1 starts at:

**0.5 tranche**

A T1 does not automatically become a full position.

---

## Stage 2 — T2

A T2 formation occurs when:

**200 SMA crosses above 350 SMA**

T2 is evaluated independently of T1.

| T2 condition                           | State              | Technical eligibility |
| -------------------------------------- | ------------------ | --------------------- |
| Fresh/developing healthy 200/350 cross | `T2_VALID`         | ✅ Yes                 |
| Fresh cross with <1.5% 200/350 gap     | `T2_FRAGILE`       | ✅ Yes                 |
| Invalid formation                      | `T2_INVALID`       | ❌ No                  |
| Cross older than 30 trading bars       | `T2_EXPIRED`       | ❌ No                  |
| Fundamental quadrant fails             | `T2_QUADRANT_FAIL` | ❌ Suppressed          |
| News/catalyst risk                     | `T2_NEWS_RISK`     | ❌ Suppressed          |
| Replaced by a later valid formation    | `T2_SUPERSEDED`    | ❌ No                  |

### T2 routing

T2 does **not** use a price-extension rejection cap.

Freshness is the primary anti-chase mechanism for T2.

If T1 is already held:

**`T2_ADD` → add 0.5 tranche**

If T1 was never held or was rejected:

**`T2_STANDALONE` → independent full-position evaluation, size 0–1.0 tranche**

T2 therefore does not require a valid T1 in order to be evaluated.

---

## Freshness

Freshness is measured in **trading bars**, not calendar days.

Default freshness window:

**30 trading bars**

A crossover is considered fresh when its crossover age is within this window.

The boundary is inclusive according to the scanner implementation.

Freshness is applied independently to T1 and T2.

---

## T1 price-extension rule

T1 has a hard anti-chase extension filter:

**Price >5% above the 50 SMA → `T1_EXTENDED`**

An extended T1 is not technically eligible for a new tranche.

This rule applies to **T1 only**.

T2 has **no equivalent price-extension cap**.

---

## Whipsaw protection

The system detects the ordering of the two crossover events.

If:

**T2 occurred before the current T1 cross**

the T1 formation is classified as:

**`T1_WHIPSAW`**

This prevents an older Stage 2 structure from being incorrectly treated as confirmation of a new Stage 1 entry.

The scanner also records:

`fast_leg_recross_while_stacked`

to identify cases where the fast leg recrosses while the longer-stage structure remains stacked.

---

## Position progression

The tranche model is:

```text
0.0 → 0.5 → 1.0
```

Typical progression:

```text
T1 valid
   ↓
0.5 tranche
   ↓
T2 valid while T1 held
   ↓
+0.5 tranche
   ↓
1.0 tranche
```

There is:

* no averaging down
* no averaging up outside the defined tranche progression
* no discretionary intermediate tranche size

Maximum position:

**1.0 tranche**

---

## Exit rules

The exit matrix is based on the corresponding SMA structure.

| Condition                   | Action          |
| --------------------------- | --------------- |
| 50 SMA falls below 200 SMA  | Exit T1 tranche |
| 200 SMA falls below 350 SMA | Exit T2 tranche |
| Both conditions occur       | `EXIT ALL`      |

These are technical exit rules.

The system does not use fundamental deterioration as a replacement for the technical exit signal.

---

## Fundamental and news filters

Fundamental data and corporate/news events are **context and risk filters**, not trading signals.

They may:

* suppress an otherwise technically eligible setup
* reduce confidence in the setup
* identify external event risk

They do not create a crossover trade by themselves.

Examples include:

* earnings
* guidance
* major corporate actions
* significant company-specific events
* relevant market/news catalysts

---

## Nifty 500 Weekly Crossover Scan

The scanner evaluates the Nifty 500 universe every Saturday.

It scans for active T1 and T2 crossover structures and highlights fresh formations within the **30-trading-bar** window.

The scan is intended to identify technically qualified candidates for subsequent risk/fundamental screening.

Output:

`crossovers.md`

Machine-readable output:

`crossovers.json`

---

## Daily Watchlist Health

For each stock in `watchlist.txt`, the daily monitor checks the active SMA structure and reports the current technical health.

The daily watchlist monitor and the weekly Nifty 500 crossover scanner serve different purposes:

* `scanner.py` → ongoing health of existing watchlist positions
* `crossover_scan.py` → discovery and classification of new T1/T2 crossover formations

---

## Setup

1. Fork or clone this repository.

2. Add stocks to `watchlist.txt`.

3. Populate `nifty500.txt` with the Nifty 500 universe.

4. Push to GitHub.

5. GitHub Actions run automatically:

   * **Daily:** watchlist health → `status.md`
   * **Weekly:** Nifty 500 crossover scan → `crossovers.md`

6. Monitor the generated Markdown and JSON files.

### Manual trigger

Go to:

**Actions → select the workflow → Run workflow**

---

## Files

| File                | Purpose                         |
| ------------------- | ------------------------------- |
| `watchlist.txt`     | Watchlist stocks                |
| `nifty500.txt`      | Nifty 500 universe              |
| `scanner.py`        | Daily watchlist health monitor  |
| `crossover_scan.py` | Weekly T1/T2 crossover scanner  |
| `status.md`         | Daily watchlist results         |
| `status.json`       | Daily machine-readable results  |
| `crossovers.md`     | Weekly crossover results        |
| `crossovers.json`   | Weekly machine-readable results |

---

## Local run

```bash
pip install -r requirements.txt

# Daily watchlist check
python scanner.py

# Weekly Nifty 500 crossover scan
python crossover_scan.py
```

---

## Technical architecture

The crossover scanner evaluates:

```text
                ┌───────────────┐
                │   Price / SMA │
                └───────┬───────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
        T1: 50/200             T2: 200/350
             │                     │
             ▼                     ▼
      State classification   State classification
             │                     │
             ▼                     ▼
       0.5 tranche          Add 0.5 / standalone
             │                     │
             └──────────┬──────────┘
                        ▼
                  0 → 0.5 → 1.0
```

The scanner records technical state, crossover age, gap classification, price-extension status, crossover ordering, and position routing so that the generated output can be audited programmatically.

---

## Important policy rules

The following are explicit v2.0 policy rules:

1. **T1 = 50/200 SMA crossover.**
2. **T2 = 200/350 SMA crossover.**
3. **T1 requires a rising 200 SMA.**
4. **Freshness = 30 trading bars.**
5. **T1 price extension >5% above 50 SMA is rejected.**
6. **T2 has no price-extension cap.**
7. **<1.5% crossover gap is classified as FRAGILE.**
8. **T2 can be evaluated independently of T1.**
9. **T1 is rejected as WHIPSAW when T2 predates the T1 crossover.**
10. **Position progression is 0 → 0.5 → 1.0.**
11. **No averaging is permitted.**
12. **Fundamentals/news are risk filters, not trading signals.**
13. **Technical eligibility does not by itself constitute an individual investment recommendation.**

---

## Disclaimer

This project is for educational and analytical purposes only.

It is not an individual investment recommendation.

Past performance does not guarantee future results.

Trading and investing involve risk, including the possible loss of capital.
