# Two-Stage Golden Cross Scanner

**Last updated:** 2026-10-03 11:02 IST
**Scanned:** 493 | **Stage 2:** 35 | **Stage 1:** 16 | **Hold:** 5 | **Wait:** 7 | **T1 Technically Eligible:** 1 | **T2 Technically Eligible:** 4 | **Skipped:** 430

**Skip breakdown:** Not qualified: 426 · Insufficient history: 3 · No data: 1 · Exceptions: 0

↑ = SMA rising (50: 5 bars, 200/350: 20 bars) · ↓ = SMA falling

> **Note:** the tables below reflect `t1_technical_eligible` / `t2_technical_eligible` (Patch B state machine), not raw freshness. A name can be `t1_fresh` and still be rejected — see the Rejected tables for why. Fundamental quadrant and news checks (`quadrant_status`, `news_status`) are never computed here — they remain a manual weekly-review step regardless of technical eligibility.

---

## 🆕 Fresh T1 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (1)

| Symbol | LTP | Price Tier | Gap Class | T1 Cross | Age | 50/200 Gap |
|--------|-----|------------|-----------|----------|-----|------------|
| GODREJAGRO | ₹631.9 | EARLY_CONFIRM | HEALTHY | 2026-09-02 | 21d | 6.11% |

### ❌ Rejected (1)

**T1_EXTENDED** (1)

| Symbol | LTP | T1 Cross | Age | Reason |
|--------|-----|----------|-----|--------|
| JYOTICNC | ₹1032.1 | 2026-08-27 | 25d | 8.73% above 50 SMA (cap: 5%) |

---

## 🆕 Fresh T2 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (4)

| Symbol | LTP | Gap Class | T2 Cross | Age | 200/350 Gap |
|--------|-----|-----------|----------|-----|-------------|
| PETRONET | ₹285.5 | FRAGILE | 2026-09-22 | 7d | 0.34% |
| REDINGTON | ₹397.95 | FRAGILE | 2026-09-22 | 7d | 0.62% |
| SHYAMMETL | ₹1047.8 | DEVELOPING | 2026-09-08 | 17d | 1.52% |
| CARBORUNIV | ₹1239.7 | DEVELOPING | 2026-09-03 | 20d | 2.21% |

> Sizing (0.5 add vs 1.0 standalone) depends on whether T1 is already held for each name — a portfolio fact this scanner does not know. Check manually before sizing.

---

## 🟢 Stage 2 — Full Position (Price > 50↑ > 200↑ > 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| PETRONET | ₹285.5 | ₹285.37 ↑ | ₹279.62 ↑ | ₹278.66 ↓ | 2026-07-28 | 47d | 2026-09-22 | 7d | 2.06% | 0.34% |
| REDINGTON | ₹397.95 | ₹360.5 ↑ | ₹272.92 ↑ | ₹271.23 ↑ | 2026-07-23 | 50d | 2026-09-22 | 7d | 32.09% | 0.62% |
| SHYAMMETL | ₹1047.8 | ₹1044.19 ↑ | ₹918.4 ↑ | ₹904.67 ↑ | 2026-06-02 | 87d | 2026-09-08 | 17d | 13.7% | 1.52% |
| CARBORUNIV | ₹1239.7 | ₹1124.91 ↑ | ₹977.16 ↑ | ₹956.02 ↑ | 2026-05-18 | 98d | 2026-09-03 | 20d | 15.12% | 2.21% |
| AKUMS | ₹813.1 | ₹749.97 ↑ | ₹575.58 ↑ | ₹540.56 ↑ | 2026-04-10 | 122d | 2026-08-05 | 41d | 30.3% | 6.48% |
| FINCABLES | ₹1458.8 | ₹1251.56 ↑ | ₹1000.59 ↑ | ₹936.05 ↑ | 2026-04-09 | 124d | 2026-07-22 | 51d | 25.08% | 6.89% |
| WELSPUNLIV | ₹239.17 | ₹191.1 ↑ | ₹149.87 ↑ | ₹141.5 ↑ | 2026-05-28 | 90d | 2026-06-24 | 71d | 27.5% | 5.92% |
| HFCL | ₹238.36 | ₹220.67 ↑ | ₹143.12 ↑ | ₹114.96 ↑ | 2026-04-20 | 118d | 2026-06-09 | 82d | 54.18% | 24.5% |
| SONACOMS | ₹805.0 | ₹796.0 ↑ | ₹614.61 ↑ | ₹552.85 ↑ | — | — | 2026-06-01 | 88d | 29.51% | 11.17% |
| IPCALAB | ₹1943.2 | ₹1885.79 ↑ | ₹1629.3 ↑ | ₹1523.71 ↑ | — | — | 2026-05-29 | 89d | 15.74% | 6.93% |
| AUROPHARMA | ₹1676.8 | ₹1646.92 ↑ | ₹1421.49 ↑ | ₹1296.46 ↑ | — | — | 2026-04-28 | 112d | 15.86% | 9.64% |
| AJANTPHARM | ₹3581.0 | ₹3530.12 ↑ | ₹3089.38 ↑ | ₹2849.35 ↑ | — | — | 2026-04-22 | 116d | 14.27% | 8.42% |
| CGCL | ₹249.23 | ₹247.18 ↑ | ₹204.58 ↑ | ₹195.08 ↑ | 2026-06-03 | 86d | 2026-03-04 | 147d | 20.82% | 4.87% |
| GLAND | ₹2874.4 | ₹2810.05 ↑ | ₹2148.15 ↑ | ₹2007.81 ↑ | 2026-05-28 | 90d | — | — | 30.81% | 6.99% |
| DIVISLAB | ₹9249.0 | ₹8848.01 ↑ | ₹7037.39 ↑ | ₹6758.5 ↑ | 2026-05-19 | 97d | — | — | 25.73% | 4.13% |
| KIRLOSENG | ₹2242.7 | ₹2160.09 ↑ | ₹1750.46 ↑ | ₹1399.59 ↑ | — | — | — | — | 23.4% | 25.07% |
| PAYTM | ₹1656.0 | ₹1613.64 ↑ | ₹1275.31 ↑ | ₹1211.39 ↑ | 2026-08-04 | 42d | — | — | 26.53% | 5.28% |
| APARINDS | ₹17648.0 | ₹16774.95 ↑ | ₹12634.18 ↑ | ₹10852.1 ↑ | — | — | — | — | 32.77% | 16.42% |
| EMCURE | ₹1944.6 | ₹1926.69 ↑ | ₹1688.68 ↑ | ₹1543.46 ↑ | — | — | — | — | 14.09% | 9.41% |
| LALPATHLAB | ₹2005.1 | ₹1911.44 ↑ | ₹1591.83 ↑ | ₹1559.68 ↑ | 2026-06-08 | 83d | — | — | 20.08% | 2.06% |
| INOXINDIA | ₹2168.3 | ₹2040.23 ↑ | ₹1564.94 ↑ | ₹1401.28 ↑ | 2026-04-13 | 122d | — | — | 30.37% | 11.68% |
| BHEL | ₹421.0 | ₹419.84 ↑ | ₹347.92 ↑ | ₹305.39 ↑ | — | — | — | — | 20.67% | 13.93% |
| LAURUSLABS | ₹1984.0 | ₹1881.41 ↑ | ₹1362.7 ↑ | ₹1139.02 ↑ | — | — | — | — | 38.07% | 19.64% |
| WELCORP | ₹2605.8 | ₹2265.95 ↑ | ₹1375.45 ↑ | ₹1160.7 ↑ | 2026-04-22 | 116d | — | — | 64.74% | 18.5% |
| APLAPOLLO | ₹2115.7 | ₹2094.24 ↑ | ₹1981.68 ↑ | ₹1868.47 ↑ | 2026-09-03 | 20d | — | — | 5.68% | 6.06% |
| MCX | ₹3204.0 | ₹3087.79 ↑ | ₹2758.64 ↑ | ₹2290.94 ↑ | — | — | — | — | 11.93% | 20.41% |
| GRAPHITE | ₹786.15 | ₹741.82 ↑ | ₹673.64 ↑ | ₹617.76 ↑ | — | — | — | — | 10.12% | 9.05% |
| ENGINERSIN | ₹312.75 | ₹258.56 ↑ | ₹225.9 ↑ | ₹216.7 ↑ | 2026-04-21 | 117d | — | — | 14.46% | 4.24% |
| ZYDUSLIFE | ₹1145.7 | ₹1141.3 ↑ | ₹1013.06 ↑ | ₹992.39 ↑ | 2026-06-02 | 87d | — | — | 12.66% | 2.08% |
| GESHIP | ₹1530.6 | ₹1379.86 ↑ | ₹1352.94 ↑ | ₹1192.2 ↑ | — | — | — | — | 1.99% | 13.48% |
| RBLBANK | ₹411.4 | ₹394.18 ↑ | ₹343.52 ↑ | ₹310.98 ↑ | — | — | — | — | 14.75% | 10.47% |
| PTCIL | ₹22025.0 | ₹20899.18 ↑ | ₹18238.26 ↑ | ₹17086.35 ↑ | 2026-06-26 | 69d | — | — | 14.59% | 6.74% |
| CUB | ₹230.04 | ₹222.27 ↑ | ₹206.5 ↑ | ₹188.0 ↑ | — | — | — | — | 7.64% | 9.84% |
| SYRMA | ₹1717.9 | ₹1519.4 ↑ | ₹1108.84 ↑ | ₹940.32 ↑ | — | — | — | — | 37.03% | 17.92% |
| VARROC | ₹830.6 | ₹808.22 ↑ | ₹627.94 ↑ | ₹607.55 ↑ | 2026-07-07 | 62d | — | — | 28.71% | 3.36% |

## 🟡 Stage 1 — Half Position (Price > 50↑ > 200↑, 200 < 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| GODREJAGRO | ₹631.9 | ₹612.71 ↑ | ₹577.44 ↑ | ₹630.03 ↓ | 2026-09-02 | 21d | 6.11% | — |
| JYOTICNC | ₹1032.1 | ₹949.26 ↑ | ₹827.53 ↑ | ₹905.78 ↓ | 2026-08-27 | 25d | 14.71% | — |
| WESTLIFE | ₹588.05 | ₹558.95 ↑ | ₹503.11 ↑ | ₹576.83 ↓ | 2026-08-18 | 32d | 11.1% | — |
| PVRINOX | ₹1215.3 | ₹1207.67 ↑ | ₹1050.82 ↑ | ₹1056.0 ↑ | 2026-08-13 | 35d | 14.93% | — |
| BEML | ₹1962.3 | ₹1927.98 ↑ | ₹1779.02 ↑ | ₹1893.28 ↑ | 2026-08-10 | 38d | 8.37% | — |
| TBOTEK | ₹1671.5 | ₹1650.54 ↑ | ₹1430.3 ↑ | ₹1445.49 ↑ | 2026-08-05 | 40d | 15.4% | — |
| CASTROLIND | ₹199.04 | ₹188.18 ↑ | ₹179.37 ↑ | ₹184.71 ↑ | 2026-07-22 | 51d | 4.92% | — |
| ACE | ₹1212.3 | ₹1139.18 ↑ | ₹961.03 ↑ | ₹1022.57 ↓ | 2026-07-16 | 55d | 18.54% | — |
| INDGN | ₹593.5 | ₹571.1 ↑ | ₹514.47 ↑ | ₹533.34 ↑ | 2026-06-23 | 72d | 11.01% | — |
| JSWINFRA | ₹357.45 | ₹337.93 ↑ | ₹292.7 ↑ | ₹295.36 ↑ | 2026-06-23 | 72d | 15.45% | — |
| MOTILALOFS | ₹989.9 | ₹965.24 ↑ | ₹858.89 ↑ | ₹877.69 ↑ | 2026-06-22 | 73d | 12.38% | — |
| RAYMOND | ₹1197.2 | ₹784.65 ↑ | ₹543.22 ↑ | ₹568.09 ↓ | 2026-06-15 | 78d | 44.45% | — |
| GNFC | ₹589.15 | ₹557.46 ↑ | ₹486.05 ↑ | ₹488.19 ↑ | 2026-06-11 | 80d | 14.69% | — |
| FINEORG | ₹5131.0 | ₹5092.56 ↑ | ₹4693.46 ↑ | ₹4708.44 ↑ | 2026-05-21 | 94d | 8.5% | — |
| MAHSEAMLES | ₹698.75 | ₹644.65 ↑ | ₹592.88 ↑ | ₹608.36 ↑ | 2026-05-07 | 105d | 8.73% | — |
| RATNAMANI | ₹2619.4 | ₹2563.07 ↑ | ₹2448.86 ↑ | ₹2492.7 ↑ | 2026-05-04 | 108d | 4.66% | — |

## 🟢 Hold — Stacked but SMAs not all rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| ADANIPORTS | ₹1737.8 | ₹1721.38 ↓ | ₹1629.05 ↑ | ₹1537.11 ↑ | — | — | — | — | 5.67% | 5.98% |
| PHOENIXLTD | ₹1930.0 | ₹1920.78 ↓ | ₹1820.23 ↑ | ₹1723.29 ↑ | — | — | — | — | 5.52% | 5.63% |
| ASAHIINDIA | ₹944.25 | ₹936.71 ↑ | ₹904.49 ↓ | ₹886.15 ↑ | 2026-09-08 | 17d | — | — | 3.56% | 2.07% |
| SCHNEIDER | ₹1275.4 | ₹1256.91 ↓ | ₹1083.57 ↑ | ₹970.83 ↑ | 2026-04-02 | 128d | — | — | 16.0% | 11.61% |
| AEGISLOG | ₹1401.1 | ₹1329.53 ↓ | ₹926.64 ↑ | ₹856.09 ↑ | 2026-06-16 | 77d | 2026-07-07 | 62d | 43.48% | 8.24% |

## ⚪ Wait — Cross active but 50 and/or 200 SMA not rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| CYIENT | ₹1104.6 | ₹985.85 ↑ | ₹959.87 ↓ | ₹1065.97 ↓ | 2026-09-24 | 5d | 2.71% | — |
| COFORGE | ₹1826.0 | ₹1817.17 ↑ | ₹1514.06 ↓ | ₹1618.94 ↑ | 2026-08-07 | 39d | 20.02% | — |
| KOTAKBANK | ₹418.35 | ₹405.47 ↑ | ₹398.8 ↓ | ₹406.69 ↓ | 2026-09-18 | 9d | 1.67% | — |
| MANKIND | ₹2535.0 | ₹2411.79 ↓ | ₹2298.06 ↑ | ₹2357.29 ↓ | 2026-06-10 | 81d | 4.95% | — |
| JUBLPHARMA | ₹999.3 | ₹958.29 ↑ | ₹952.49 ↓ | ₹1017.78 ↑ | 2026-09-24 | 5d | 0.61% | — |
| KAJARIACER | ₹1225.1 | ₹1212.56 ↓ | ₹1090.47 ↑ | ₹1108.24 ↑ | 2026-06-03 | 85d | 11.2% | — |
| MANYAVAR | ₹519.2 | ₹518.57 ↑ | ₹455.42 ↓ | ₹564.3 ↓ | 2026-09-04 | 19d | 13.87% | — |

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
