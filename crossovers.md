# Two-Stage Golden Cross Scanner

**Last updated:** 2026-10-17 10:16 IST
**Scanned:** 493 | **Stage 2:** 34 | **Stage 1:** 7 | **Hold:** 6 | **Wait:** 17 | **T1 Technically Eligible:** 0 | **T2 Technically Eligible:** 6 | **Skipped:** 429

**Skip breakdown:** Not qualified: 425 · Insufficient history: 3 · No data: 1 · Exceptions: 0

↑ = SMA rising (50: 5 bars, 200/350: 20 bars) · ↓ = SMA falling

> **Note:** the tables below reflect `t1_technical_eligible` / `t2_technical_eligible` (Patch B state machine), not raw freshness. A name can be `t1_fresh` and still be rejected — see the Rejected tables for why. Fundamental quadrant and news checks (`quadrant_status`, `news_status`) are never computed here — they remain a manual weekly-review step regardless of technical eligibility.

---

## 🆕 Fresh T1 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (0)

*None this week*

---

## 🆕 Fresh T2 (last 30 trading bars, Strict gate)

### ✅ Technically Eligible (6)

| Symbol | LTP | Gap Class | T2 Cross | Age | 200/350 Gap |
|--------|-----|-----------|----------|-----|-------------|
| FINEORG | ₹5402.5 | FRAGILE | 2026-10-13 | 2d | 0.17% |
| PETRONET | ₹295.2 | FRAGILE | 2026-09-25 | 13d | 0.64% |
| BALRAMCHIN | ₹721.15 | DEVELOPING | 2026-09-28 | 13d | 2.16% |
| REDINGTON | ₹383.5 | DEVELOPING | 2026-09-16 | 21d | 1.6% |
| SHYAMMETL | ₹1198.5 | DEVELOPING | 2026-09-10 | 24d | 2.22% |
| JINDALSAW | ₹301.55 | HEALTHY | 2026-09-03 | 29d | 6.54% |

> Sizing (0.5 add vs 1.0 standalone) depends on whether T1 is already held for each name — a portfolio fact this scanner does not know. Check manually before sizing.

---

## 🟢 Stage 2 — Full Position (Price > 50↑ > 200↑ > 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| FINEORG | ₹5402.5 | ₹5202.89 ↑ | ₹4737.7 ↑ | ₹4729.89 ↑ | 2026-05-22 | 100d | 2026-10-13 | 2d | 9.82% | 0.17% |
| PETRONET | ₹295.2 | ₹287.65 ↑ | ₹280.43 ↑ | ₹278.64 ↓ | 2026-07-30 | 53d | 2026-09-25 | 13d | 2.57% | 0.64% |
| BALRAMCHIN | ₹721.15 | ₹677.59 ↑ | ₹549.29 ↑ | ₹537.7 ↑ | 2026-04-30 | 116d | 2026-09-28 | 13d | 23.36% | 2.16% |
| REDINGTON | ₹383.5 | ₹376.06 ↑ | ₹279.14 ↑ | ₹274.74 ↑ | 2026-07-27 | 57d | 2026-09-16 | 21d | 34.72% | 1.6% |
| SHYAMMETL | ₹1198.5 | ₹1057.19 ↑ | ₹929.53 ↑ | ₹909.34 ↑ | 2026-06-04 | 93d | 2026-09-10 | 24d | 13.73% | 2.22% |
| JINDALSAW | ₹301.55 | ₹287.75 ↑ | ₹232.85 ↑ | ₹218.56 ↑ | 2026-04-21 | 123d | 2026-09-03 | 29d | 23.58% | 6.54% |
| PNBHOUSING | ₹1183.9 | ₹1148.77 ↑ | ₹996.3 ↑ | ₹965.33 ↑ | 2026-05-13 | 107d | 2026-08-10 | 46d | 15.3% | 3.21% |
| FINCABLES | ₹1393.9 | ₹1325.42 ↑ | ₹1022.72 ↑ | ₹946.45 ↑ | 2026-04-09 | 129d | 2026-07-28 | 55d | 29.6% | 8.06% |
| AARTIIND | ₹505.05 | ₹501.0 ↑ | ₹456.57 ↑ | ₹435.31 ↑ | — | — | 2026-07-22 | 59d | 9.73% | 4.88% |
| AEGISLOG | ₹1366.7 | ₹1347.04 ↑ | ₹955.71 ↑ | ₹870.72 ↑ | 2026-06-17 | 84d | 2026-07-08 | 70d | 40.95% | 9.76% |
| WELSPUNLIV | ₹219.3 | ₹203.56 ↑ | ₹153.96 ↑ | ₹143.67 ↑ | 2026-06-01 | 96d | 2026-06-25 | 78d | 32.22% | 7.16% |
| HFCL | ₹256.01 | ₹232.43 ↑ | ₹150.43 ↑ | ₹118.75 ↑ | 2026-04-20 | 124d | 2026-06-11 | 88d | 54.51% | 26.68% |
| ANGELONE | ₹300.0 | ₹293.38 ↑ | ₹287.8 ↑ | ₹274.58 ↑ | 2026-04-20 | 124d | 2026-05-13 | 108d | 1.94% | 4.82% |
| AUROPHARMA | ₹1666.9 | ₹1666.43 ↑ | ₹1438.89 ↑ | ₹1306.44 ↑ | — | — | 2026-04-28 | 118d | 15.81% | 10.14% |
| ADANIPORTS | ₹1743.2 | ₹1725.77 ↑ | ₹1635.59 ↑ | ₹1542.4 ↑ | — | — | — | — | 5.51% | 6.04% |
| CRAFTSMAN | ₹10941.0 | ₹10772.27 ↑ | ₹8821.97 ↑ | ₹7796.71 ↑ | — | — | — | — | 22.11% | 13.15% |
| GLAND | ₹3066.3 | ₹2905.32 ↑ | ₹2197.97 ↑ | ₹2039.41 ↑ | 2026-05-29 | 96d | — | — | 32.18% | 7.77% |
| DIVISLAB | ₹9144.5 | ₹9098.16 ↑ | ₹7164.28 ↑ | ₹6833.29 ↑ | 2026-05-19 | 104d | — | — | 26.99% | 4.84% |
| KPIL | ₹1395.7 | ₹1391.62 ↑ | ₹1254.8 ↑ | ₹1231.9 ↑ | 2026-06-02 | 94d | — | — | 10.9% | 1.86% |
| PAYTM | ₹1693.5 | ₹1673.21 ↑ | ₹1294.66 ↑ | ₹1230.33 ↑ | 2026-08-05 | 50d | — | — | 29.24% | 5.23% |
| BHEL | ₹434.6 | ₹425.58 ↑ | ₹353.61 ↑ | ₹309.22 ↑ | — | — | — | — | 20.35% | 14.36% |
| LAURUSLABS | ₹2018.5 | ₹1925.61 ↑ | ₹1398.67 ↑ | ₹1165.83 ↑ | — | — | — | — | 37.67% | 19.97% |
| WELCORP | ₹2571.5 | ₹2438.19 ↑ | ₹1449.7 ↑ | ₹1203.48 ↑ | 2026-04-22 | 122d | — | — | 68.19% | 20.46% |
| APLAPOLLO | ₹2139.0 | ₹2136.7 ↑ | ₹1993.72 ↑ | ₹1876.02 ↑ | 2026-09-02 | 29d | — | — | 7.17% | 6.27% |
| SOLARINDS | ₹20011.0 | ₹19997.68 ↑ | ₹16596.32 ↑ | ₹15738.11 ↑ | 2026-04-27 | 119d | — | — | 20.49% | 5.45% |
| GRAPHITE | ₹770.25 | ₹765.47 ↑ | ₹683.23 ↑ | ₹624.0 ↑ | — | — | — | — | 12.04% | 9.49% |
| ENGINERSIN | ₹273.45 | ₹271.57 ↑ | ₹229.74 ↑ | ₹219.02 ↑ | 2026-04-21 | 123d | — | — | 18.21% | 4.89% |
| KARURVYSYA | ₹345.65 | ₹335.55 ↑ | ₹303.76 ↑ | ₹268.14 ↑ | — | — | — | — | 10.47% | 13.28% |
| GESHIP | ₹1507.4 | ₹1410.41 ↑ | ₹1367.57 ↑ | ₹1203.73 ↑ | — | — | — | — | 3.13% | 13.61% |
| PTCIL | ₹25045.0 | ₹21975.94 ↑ | ₹18536.29 ↑ | ₹17307.45 ↑ | 2026-06-29 | 76d | — | — | 18.56% | 7.1% |
| CUB | ₹227.38 | ₹224.52 ↑ | ₹207.47 ↑ | ₹189.72 ↑ | — | — | — | — | 8.22% | 9.36% |
| NYKAA | ₹345.0 | ₹334.05 ↑ | ₹288.59 ↑ | ₹264.26 ↑ | — | — | — | — | 15.75% | 9.21% |
| SYRMA | ₹1604.6 | ₹1582.53 ↑ | ₹1146.66 ↑ | ₹965.35 ↑ | — | — | — | — | 38.01% | 18.78% |
| MRPL | ₹172.71 | ₹172.36 ↑ | ₹168.12 ↑ | ₹156.3 ↑ | 2026-09-02 | 30d | — | — | 2.53% | 7.56% |

## 🟡 Stage 1 — Half Position (Price > 50↑ > 200↑, 200 < 350)

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| JYOTICNC | ₹997.2 | ₹985.51 ↑ | ₹834.22 ↑ | ₹904.75 ↓ | 2026-08-28 | 33d | 18.14% | — |
| PVRINOX | ₹1381.9 | ₹1242.79 ↑ | ₹1063.51 ↑ | ₹1064.12 ↑ | 2026-08-14 | 42d | 16.86% | — |
| CASTROLIND | ₹196.23 | ₹191.13 ↑ | ₹180.26 ↑ | ₹184.93 ↑ | 2026-07-24 | 57d | 6.03% | — |
| INDGN | ₹598.3 | ₹584.14 ↑ | ₹517.65 ↑ | ₹534.05 ↑ | 2026-06-24 | 79d | 12.85% | — |
| MOTILALOFS | ₹1062.95 | ₹995.76 ↑ | ₹866.19 ↑ | ₹883.28 ↑ | 2026-06-23 | 79d | 14.96% | — |
| HAL | ₹4989.0 | ₹4850.24 ↑ | ₹4419.15 ↑ | ₹4515.91 ↑ | 2026-06-23 | 80d | 9.75% | — |
| RAYMOND | ₹1142.1 | ₹886.26 ↑ | ₹573.51 ↑ | ₹582.84 ↓ | 2026-06-16 | 84d | 54.53% | — |

## 🟢 Hold — Stacked but SMAs not all rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | T2 Cross | T2 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|----------|--------|------------|-------------|
| ADANIGREEN | ₹1302.0 | ₹1300.64 ↓ | ₹1210.36 ↑ | ₹1125.54 ↑ | 2026-05-06 | 113d | 2026-04-21 | 123d | 7.46% | 7.54% |
| GAEL | ₹173.7 | ₹167.66 ↓ | ₹152.57 ↑ | ₹134.22 ↑ | — | — | 2026-03-27 | 136d | 9.89% | 13.67% |
| PHOENIXLTD | ₹1917.2 | ₹1906.31 ↓ | ₹1822.33 ↑ | ₹1728.85 ↑ | — | — | — | — | 4.61% | 5.41% |
| PNB | ₹116.3 | ₹115.79 ↑ | ₹112.4 ↓ | ₹110.81 ↑ | 2026-09-11 | 23d | — | — | 3.02% | 1.44% |
| GPPL | ₹168.09 | ₹161.0 ↑ | ₹157.54 ↓ | ₹155.59 ↑ | 2026-10-07 | 6d | — | — | 2.19% | 1.25% |
| TECHM | ₹1790.0 | ₹1576.97 ↓ | ₹1493.18 ↑ | ₹1484.51 ↑ | 2026-07-30 | 54d | 2026-07-23 | 59d | 5.61% | 0.58% |

## ⚪ Wait — Cross active but 50 and/or 200 SMA not rising

| Symbol | LTP | SMA 50 | SMA 200 | SMA 350 | T1 Cross | T1 Age | 50/200 Gap | 200/350 Gap |
|--------|-----|--------|---------|---------|----------|--------|------------|-------------|
| CYIENT | ₹1194.5 | ₹1042.06 ↑ | ₹964.51 ↓ | ₹1066.54 ↓ | 2026-09-28 | 13d | 8.04% | — |
| COFORGE | ₹1951.9 | ₹1853.08 ↑ | ₹1524.06 ↓ | ₹1627.38 ↑ | 2026-08-10 | 47d | 21.59% | — |
| FSL | ₹281.8 | ₹268.74 ↓ | ₹260.69 ↓ | ₹298.45 ↓ | 2026-09-09 | 25d | 3.09% | — |
| TRENT | ₹2958.7 | ₹2858.24 ↓ | ₹2808.55 ↓ | ₹3766.11 ↓ | 2026-09-25 | 14d | 1.77% | — |
| INDHOTEL | ₹772.1 | ₹725.64 ↓ | ₹687.15 ↑ | ₹711.9 ↓ | 2026-07-17 | 63d | 5.6% | — |
| KOTAKBANK | ₹447.4 | ₹414.28 ↑ | ₹399.76 ↓ | ₹407.47 ↓ | 2026-09-21 | 18d | 3.63% | — |
| NUVOCO | ₹335.9 | ₹329.64 ↓ | ₹326.5 ↓ | ₹355.87 ↓ | 2026-08-26 | 34d | 0.96% | — |
| BAJAJHLDNG | ₹11225.0 | ₹11093.3 ↓ | ₹10532.08 ↓ | ₹11458.76 ↓ | 2026-08-14 | 42d | 5.33% | — |
| TATACOMM | ₹1742.8 | ₹1709.98 ↓ | ₹1691.61 ↓ | ₹1703.42 ↑ | 2026-06-16 | 85d | 1.09% | — |
| TANLA | ₹559.65 | ₹531.54 ↓ | ₹508.14 ↓ | ₹556.48 ↑ | 2026-07-16 | 64d | 4.6% | — |
| MPHASIS | ₹2500.0 | ₹2380.13 ↑ | ₹2344.22 ↓ | ₹2494.2 ↓ | 2026-09-16 | 21d | 1.53% | — |
| PERSISTENT | ₹5741.0 | ₹5549.6 ↑ | ₹5329.78 ↓ | ₹5471.14 ↑ | 2026-09-16 | 21d | 4.12% | — |
| ICICIBANK | ₹1397.0 | ₹1384.22 ↓ | ₹1345.5 ↓ | ₹1365.17 ↓ | 2026-07-29 | 55d | 2.88% | — |
| DLF | ₹675.0 | ₹663.91 ↑ | ₹621.63 ↓ | ₹681.85 ↓ | 2026-08-14 | 43d | 6.8% | — |
| JUSTDIAL | ₹713.25 | ₹674.84 ↓ | ₹619.38 ↓ | ₹708.44 ↓ | 2026-08-17 | 42d | 8.95% | — |
| SAREGAMA | ₹504.0 | ₹502.08 ↓ | ₹418.32 ↑ | ₹437.98 ↓ | 2026-06-19 | 82d | 20.03% | — |
| ECLERX | ₹1998.2 | ₹1888.36 ↑ | ₹1767.82 ↓ | ₹1881.49 ↑ | 2026-09-09 | 24d | 6.82% | — |

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
