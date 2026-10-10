# Two-Stage Golden Cross Scanner

**Last updated:** 2026-10-10 11:37 IST
**Scanned:** 493 | **Stage 2:** 38 | **Stage 1:** 11 | **Hold:** 3 | **Wait:** 6 | **T1 Technically Eligible:** 2 | **T2 Technically Eligible:** 5 | **Skipped:** 435

**Skip breakdown:** Not qualified: 431 · Insufficient history: 3 · No data: 1 · Exceptions: 0

↑ = SMA rising (50: 5 bars, 200/350: 20 bars) · ↓ = SMA falling

> **Note:** the tables below reflect `t1_technical_eligible` / `t2_technical_eligible` (Patch B state machine), not raw freshness. A name can be `t1_fresh` and still be rejected — see the Rejected tables for why. Fundamental quadrant and news checks (`quadrant_status`, `news_status`) are never computed here — they remain a manual weekly-review step regardless of technical eligibility.

---

## 🆕 Fresh T1 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (2)

| Symbol | LTP | Price Tier | Gap Class | T1 Cross | Age | 50/200 Gap |
|--------|-----|------------|-----------|----------|-----|------------|
| GODREJAGRO | ₹628.45 | FRESH_CROSS | HEALTHY | 2026-09-02 | 25d | 6.81% |
| JYOTICNC | ₹1009.9 | EARLY_CONFIRM | HEALTHY | 2026-08-28 | 27d | 15.91% |

---

## 🆕 Fresh T2 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (5)

| Symbol | LTP | Gap Class | T2 Cross | Age | 200/350 Gap |
|--------|-----|-----------|----------|-----|-------------|
| PETRONET | ₹288.5 | FRAGILE | 2026-09-25 | 8d | 0.38% |
| BALRAMCHIN | ₹678.15 | FRAGILE | 2026-09-28 | 8d | 1.32% |
| REDINGTON | ₹380.0 | FRAGILE | 2026-09-16 | 16d | 1.11% |
| SHYAMMETL | ₹1066.8 | DEVELOPING | 2026-09-10 | 18d | 1.6% |
| CARBORUNIV | ₹1202.6 | DEVELOPING | 2026-09-08 | 21d | 2.5% |

> Sizing (0.5 add vs 1.0 standalone) depends on whether T1 is already held for each name — a portfolio fact this scanner does not know. Check manually before sizing.

---

## 🟢 Stage 2 — Full Position (Price > 50↑ > 200↑ > 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| PETRONET | ₹288.5 | ₹286.58 ↑ | ₹279.89 ↑ | ₹278.82 ↓ | 2026-07-30 | 48d | 2026-09-25 | 8d | 2.39% | 0.38% |
| BALRAMCHIN | ₹678.15 | ₹668.42 ↑ | ₹542.44 ↑ | ₹535.35 ↑ | 2026-04-30 | 111d | 2026-09-28 | 8d | 23.22% | 1.32% |
| REDINGTON | ₹380.0 | ₹370.43 ↑ | ₹276.03 ↑ | ₹273.01 ↑ | 2026-07-27 | 52d | 2026-09-16 | 16d | 34.2% | 1.11% |
| SHYAMMETL | ₹1066.8 | ₹1045.23 ↑ | ₹920.15 ↑ | ₹905.68 ↑ | 2026-06-04 | 87d | 2026-09-10 | 18d | 13.59% | 1.6% |
| CARBORUNIV | ₹1202.6 | ₹1142.63 ↑ | ₹982.91 ↑ | ₹958.97 ↑ | 2026-05-18 | 100d | 2026-09-08 | 21d | 16.25% | 2.5% |
| PNBHOUSING | ₹1150.0 | ₹1135.36 ↑ | ₹989.23 ↑ | ₹963.31 ↑ | 2026-05-13 | 102d | 2026-08-10 | 41d | 14.77% | 2.69% |
| AKUMS | ₹786.7 | ₹758.44 ↑ | ₹580.02 ↑ | ₹542.86 ↑ | 2026-04-10 | 123d | 2026-08-07 | 42d | 30.76% | 6.85% |
| FINCABLES | ₹1388.7 | ₹1288.84 ↑ | ₹1009.44 ↑ | ₹940.67 ↑ | 2026-04-09 | 125d | 2026-07-28 | 51d | 27.68% | 7.31% |
| AEGISLOG | ₹1382.3 | ₹1336.19 ↑ | ₹935.15 ↑ | ₹860.95 ↑ | 2026-06-17 | 78d | 2026-07-08 | 64d | 42.88% | 8.62% |
| WELSPUNLIV | ₹223.75 | ₹197.04 ↑ | ₹151.75 ↑ | ₹142.55 ↑ | 2026-06-01 | 91d | 2026-06-25 | 73d | 29.84% | 6.46% |
| HFCL | ₹260.4 | ₹226.66 ↑ | ₹145.63 ↑ | ₹116.33 ↑ | 2026-04-20 | 119d | 2026-06-11 | 83d | 55.64% | 25.18% |
| IPCALAB | ₹1915.4 | ₹1898.61 ↑ | ₹1637.24 ↑ | ₹1528.33 ↑ | — | — | 2026-06-02 | 90d | 15.96% | 7.13% |
| AUROPHARMA | ₹1693.0 | ₹1656.65 ↑ | ₹1427.24 ↑ | ₹1299.62 ↑ | — | — | 2026-04-28 | 113d | 16.07% | 9.82% |
| GLAND | ₹3079.1 | ₹2850.93 ↑ | ₹2162.62 ↑ | ₹2016.08 ↑ | 2026-05-29 | 91d | — | — | 31.83% | 7.27% |
| DIVISLAB | ₹9340.0 | ₹9004.83 ↑ | ₹7095.79 ↑ | ₹6792.99 ↑ | 2026-05-19 | 99d | — | — | 26.9% | 4.46% |
| KIRLOSENG | ₹2210.4 | ₹2162.59 ↑ | ₹1759.08 ↑ | ₹1405.97 ↑ | — | — | — | — | 22.94% | 25.12% |
| CHENNPETRO | ₹1487.7 | ₹1395.62 ↑ | ₹1069.47 ↑ | ₹923.22 ↑ | — | — | — | — | 30.5% | 15.84% |
| KPIL | ₹1391.9 | ₹1381.7 ↑ | ₹1249.45 ↑ | ₹1227.88 ↑ | 2026-06-02 | 90d | — | — | 10.58% | 1.76% |
| APARINDS | ₹17984.0 | ₹17125.23 ↑ | ₹12745.08 ↑ | ₹10920.9 ↑ | — | — | — | — | 34.37% | 16.7% |
| INOXINDIA | ₹2056.9 | ₹2046.83 ↑ | ₹1575.52 ↑ | ₹1407.55 ↑ | 2026-04-13 | 123d | — | — | 29.91% | 11.93% |
| BHEL | ₹433.6 | ₹422.19 ↑ | ₹349.48 ↑ | ₹306.39 ↑ | — | — | — | — | 20.81% | 14.06% |
| LAURUSLABS | ₹2036.6 | ₹1907.11 ↑ | ₹1378.69 ↑ | ₹1149.32 ↑ | — | — | — | — | 38.33% | 19.96% |
| WELCORP | ₹2640.4 | ₹2344.78 ↑ | ₹1403.5 ↑ | ₹1176.79 ↑ | 2026-04-22 | 117d | — | — | 67.07% | 19.26% |
| SOLARINDS | ₹19870.0 | ₹19793.98 ↑ | ₹16356.67 ↑ | ₹15629.1 ↑ | 2026-04-27 | 113d | — | — | 21.01% | 4.66% |
| MCX | ₹3318.2 | ₹3133.05 ↑ | ₹2769.7 ↑ | ₹2299.46 ↑ | — | — | — | — | 13.12% | 20.45% |
| RRKABEL | ₹2696.4 | ₹2645.77 ↑ | ₹1962.75 ↑ | ₹1685.56 ↑ | — | — | — | — | 34.8% | 16.45% |
| GRAPHITE | ₹802.15 | ₹751.7 ↑ | ₹675.84 ↑ | ₹619.02 ↑ | — | — | — | — | 11.22% | 9.18% |
| ENGINERSIN | ₹293.1 | ₹265.6 ↑ | ₹227.5 ↑ | ₹217.65 ↑ | 2026-04-21 | 118d | — | — | 16.75% | 4.53% |
| GESHIP | ₹1533.7 | ₹1395.58 ↑ | ₹1356.43 ↑ | ₹1194.78 ↑ | — | — | — | — | 2.89% | 13.53% |
| RBLBANK | ₹418.0 | ₹398.2 ↑ | ₹345.02 ↑ | ₹312.08 ↑ | — | — | — | — | 15.42% | 10.55% |
| PTCIL | ₹24470.0 | ₹21252.2 ↑ | ₹18343.24 ↑ | ₹17146.34 ↑ | 2026-06-29 | 71d | — | — | 15.86% | 6.98% |
| CUB | ₹231.42 | ₹222.23 ↑ | ₹207.03 ↑ | ₹188.48 ↑ | — | — | — | — | 7.34% | 9.84% |
| NYKAA | ₹343.0 | ₹333.89 ↑ | ₹286.41 ↑ | ₹262.25 ↑ | — | — | — | — | 16.58% | 9.21% |
| MAHABANK | ₹83.16 | ₹81.71 ↑ | ₹74.79 ↑ | ₹66.02 ↑ | — | — | — | — | 9.25% | 13.28% |
| NAVINFLUOR | ₹8417.5 | ₹8310.67 ↑ | ₹7049.11 ↑ | ₹6166.51 ↑ | — | — | — | — | 17.9% | 14.31% |
| SYRMA | ₹1719.9 | ₹1553.3 ↑ | ₹1122.73 ↑ | ₹948.8 ↑ | — | — | — | — | 38.35% | 18.33% |
| MRPL | ₹172.13 | ₹171.74 ↑ | ₹167.3 ↑ | ₹155.72 ↑ | 2026-09-02 | 25d | — | — | 2.66% | 7.44% |
| USHAMART | ₹503.95 | ₹502.89 ↑ | ₹461.77 ↑ | ₹430.39 ↑ | 2026-04-29 | 111d | — | — | 8.9% | 7.29% |

## 🟡 Stage 1 — Half Position (Price > 50↑ > 200↑, 200 < 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| GODREJAGRO | ₹628.45 | ₹618.08 ↑ | ₹578.67 ↑ | ₹630.33 ↓ | 2026-09-02 | 25d | 6.81% | — |
| JYOTICNC | ₹1009.9 | ₹965.12 ↑ | ₹832.68 ↑ | ₹908.73 ↓ | 2026-08-28 | 27d | 15.91% | — |
| WESTLIFE | ₹577.2 | ₹566.75 ↑ | ₹504.85 ↑ | ₹577.83 ↓ | 2026-08-19 | 34d | 12.26% | — |
| PVRINOX | ₹1309.2 | ₹1219.5 ↑ | ₹1055.24 ↑ | ₹1058.52 ↑ | 2026-08-14 | 37d | 15.57% | — |
| CASTROLIND | ₹194.67 | ₹189.89 ↑ | ₹179.82 ↑ | ₹184.91 ↑ | 2026-07-24 | 53d | 5.6% | — |
| ACE | ₹1179.8 | ₹1151.33 ↑ | ₹966.05 ↑ | ₹1025.43 ↓ | 2026-07-20 | 56d | 19.18% | — |
| INDGN | ₹580.1 | ₹578.42 ↑ | ₹516.13 ↑ | ₹534.17 ↑ | 2026-06-24 | 74d | 12.07% | — |
| MOTILALOFS | ₹1014.3 | ₹976.25 ↑ | ₹861.43 ↑ | ₹879.14 ↑ | 2026-06-23 | 74d | 13.33% | — |
| RAYMOND | ₹1167.1 | ₹828.77 ↑ | ₹555.1 ↑ | ₹574.88 ↓ | 2026-06-16 | 79d | 49.3% | — |
| GNFC | ₹592.7 | ₹567.12 ↑ | ₹488.62 ↑ | ₹489.68 ↑ | 2026-06-15 | 81d | 16.07% | — |
| FINEORG | ₹5380.5 | ₹5144.43 ↑ | ₹4708.15 ↑ | ₹4716.91 ↑ | 2026-05-22 | 95d | 9.27% | — |

## 🟢 Hold — Stacked but SMAs not all rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| PNB | ₹116.98 | ₹115.44 ↑ | ₹112.41 ↓ | ₹110.5 ↑ | 2026-09-11 | 18d | — | — | 2.7% | 1.73% |
| GPPL | ₹166.64 | ₹158.51 ↑ | ₹157.93 ↓ | ₹155.04 ↑ | 2026-10-07 | 1d | — | — | 0.37% | 1.86% |
| NUVAMA | ₹1764.4 | ₹1736.35 ↓ | ₹1529.34 ↑ | ₹1470.37 ↑ | 2026-06-03 | 89d | — | — | 13.54% | 4.01% |

## ⚪ Wait — Cross active but 50 and/or 200 SMA not rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| CYIENT | ₹1158.8 | ₹1009.61 ↑ | ₹963.6 ↓ | ₹1067.76 ↓ | 2026-09-28 | 8d | 4.77% | — |
| COFORGE | ₹1867.9 | ₹1836.38 ↑ | ₹1521.34 ↓ | ₹1623.56 ↑ | 2026-08-10 | 42d | 20.71% | — |
| TRENT | ₹2918.2 | ₹2868.47 ↓ | ₹2838.38 ↓ | ₹3802.59 ↓ | 2026-09-25 | 9d | 1.06% | — |
| KOTAKBANK | ₹441.0 | ₹409.47 ↑ | ₹399.46 ↓ | ₹407.12 ↓ | 2026-09-21 | 13d | 2.5% | — |
| LICHSGFIN | ₹537.0 | ₹526.88 ↓ | ₹524.49 ↑ | ₹541.8 ↓ | 2026-09-09 | 19d | 0.46% | — |
| PERSISTENT | ₹5770.0 | ₹5517.67 ↑ | ₹5342.79 ↓ | ₹5467.74 ↑ | 2026-09-16 | 16d | 3.27% | — |

---

<details>
<summary>System Rules</summary>

| Status | Condition | Action | Position |
|--------|-----------|--------|----------|
| 🟡 Stage 1 | Price > 50 > 200, 200 < 350, 50↑ 200↑ | Technical formation only | — |
| 🟢 Stage 2 | Price > 50 > 200 > 350, 50↑ 200↑ | Technical formation only | — |
| ⚪ Wait | Cross active but SMA not rising | No action | — |

**T1 state (evaluated in this priority order — first match wins):**
| State | Meaning |
|-------|---------|
| T1_INVALID | 50 and/or 200 SMA not rising (fails Strict gate) |
| T1_EXPIRED | Cross exists but is stale (outside 30-bar freshness window) |
| T1_EXTENDED | Price >5% above 50 SMA — outside the early-entry band |
| T1_WHIPSAW | Otherwise eligible, but a prior T2 cross predates this T1 (reverted-stack re-entry) |
| T1_FRAGILE | Eligible — 50/200 gap <1.5%, flagged as fragile |
| T1_VALID | Eligible — clean transition |

**T2 state:**
| State | Meaning |
|-------|---------|
| T2_INVALID | 50 and/or 200 SMA not rising |
| T2_EXPIRED | Cross exists but is stale |
| T2_FRAGILE | Eligible — 200/350 gap <1.5% |
| T2_VALID | Eligible — Developing or Healthy gap |

Only `T1_VALID`/`T1_FRAGILE` and `T2_VALID`/`T2_FRAGILE` are technically eligible. Technical eligibility is necessary but not sufficient — the Fundamental Quadrant Gate and news/catalyst check (never computed by this scanner) still apply before any entry decision.

**SMA Direction:** 50 SMA vs 5 trading bars ago · 200/350 SMA vs 20 trading bars ago

**Skip reasons:**
| Reason | Meaning |
|--------|---------|
| not_qualified | Real data, just not in a Price>50>200 setup right now (expected/normal) |
| insufficient_history | Fewer than 360 bars or 21 clean SMA rows — too-new listing or data gap |
| no_data | yfinance returned nothing for this symbol |
| exception | Genuine script/API failure — worth investigating |

**Exit Rules:**
| | Exit trigger | Action |
|--|-------------|--------|
| T1 | 50 SMA crosses below 200 SMA | Sell tranche 1 |
| T2 | 200 SMA crosses below 350 SMA | Sell tranche 2 |

</details>
