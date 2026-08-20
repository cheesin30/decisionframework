# The Long Game — Data & Compliance Verification Checklist

Everything in this prototype that must be verified or signed off **before any
real audience, client, or external use**. Hand the Data section to whoever owns
fund/market data; hand the Compliance section to the review team. Each item
says exactly what to check, against what, and why it matters.

Status date: July 2026 · Owner: _____________ · Target sign-off date: _____________

---

## 1 · Data verification (blocking)

All market/fund numbers in the games were **transcribed by hand from
screenshots** of source spreadsheets, then internally cross-validated (index
levels vs. stated returns agree on every row). Internal consistency is NOT
source verification — each series below needs a direct comparison against the
system of record.

### 1.1 American Balanced Fund net composite ⚠️ SUSPECTED DATA PROBLEM — highest priority

| | |
|---|---|
| **What** | Monthly net-of-fees composite (source spreadsheet col F) and its 60/40 benchmark (col G), Jan 2005 – Dec 2025, index levels base 100 |
| **Where used** | `long-term-investing-game.html` (`AMBAL_NET`, `AMBAL_BENCH`). The Sales edition (`long-term-game-sales.html`, `AMBAL_NET_2020`) **no longer uses the transcribed composite** — see the rebuilt-series row below. |
| **The problem** | As transcribed, the fund's **net** return trails its own benchmark by ≈1%/yr over the full record — cumulative **+313.7% (7.00%/yr) vs +401.9% (7.98%/yr)**, and **+64.2% vs +72.3%** over 2020–2025. A ~1%/yr drag is larger than the fund's published expense ratio (≈0.57% for ABALX) and inconsistent with the fund's actual long-term record — strongly suggesting a wrong share class, a gross/net mix-up, or a transcription error in the source column. |
| **Consequence** | The transcribed composite was **removed from the Sales edition** (Jul 2026). Its fund line now uses the **real monthly series** (next row). |
| **Real monthly series (Jul 2026)** | Sales `AMBAL_NET_2020` is now ABALX's **actual monthly net total returns**: month-end **dividend-adjusted closing prices** (Class A at NAV, distributions reinvested), Dec 2019 – Dec 2025, indexed to 100 at 2019-12. Source: Nasdaq month-end adjusted-close (screenshots supplied Jul 2026), transcribed as 73 adjusted-close points. **Validation**: each calendar year compounds to the fund's published annual total return within rounding (computed 2020 +10.85 / 2021 +15.76 / 2022 −12.15 / 2023 +14.04 / 2024 +14.98 / 2025 +18.46 vs published +10.86 / +15.76 / −12.11 / +14.01 / +14.95 / +18.47; largest gap 0.04pp). Full-period +75.1% (9.79%/yr). **Still to do**: confirm the adjusted-close series against the fund's own books/prospectus and obtain compliance review before client use. **Note**: compounding these actual months gives a 5-yr (2021–25) of +9.58%/yr vs the +9.73% standardized 5-yr in the fact panel — reconcile the small difference (rounding / as-of window) at verification. |
| **Verify** | ① Which share class / fee basis col F actually represents. ② The correct monthly net TR series from the system of record. ③ Fund facts for the Sales panel — **now populated from publicly available fund information (Jul 2026): ABALX, Class A, 0.55% net expense ratio, inception 7/26/1975, standardized returns as of 12/31/2025 (1yr +18.47% / 5yr +9.73% / 10yr +10.42% at NAV)** — confirm against the current prospectus/fact sheet before client use. |
| **New evidence (Jul 2026)** | The published ABALX standardized returns **beat** the 60/40 benchmark on 1/5/10-yr horizons (+18.47 vs +13.70, +9.73 vs +8.47, +10.42 vs +9.78), the opposite of the transcribed composite's behavior — further confirming the composite series, not the fund, is wrong. |

### 1.2 Derived S&P 500 series, 2020–2025

| | |
|---|---|
| **What** | 72 monthly S&P 500 total returns derived as `(benchmark − 0.4 × Agg) / 0.6` from the AMBAL benchmark and the Bloomberg Aggregate |
| **Where used** | `EQ_2020` in the 2020-2025, Learning, Sales, and Live editions (drives play + reveal) |
| **Already checked** | Matches known real S&P monthly figures within 0.05 pp on 9 reference months (e.g. 2020-03 −12.4%, 2020-04 +12.8%, 2020-11 +10.9%, 2022-09 −9.2%, 2023-11 +9.1%) |
| **Verify** | Full 72-month series against the S&P 500 TR index directly (not via the decomposition) |

### 1.3 Bloomberg U.S. Aggregate, 2020–2025

`AGG_2020`, 72 monthly total returns, same four files. Verify against the index
provider's monthly TR series.

### 1.4 60/40 benchmark monthly series, 2005–2025

`BENCH_0525`, 251 monthly returns (2005-02 – 2025-12), used by the "History
rhymes" era flip (GFC / Euro-debt / China-2018 eras) and the headline stat
($250,945 stayed invested vs $135,882 missing the 10 best months). Landmark
check passed (2008-10 = −11.02%). Verify the full series against col G source.

### 1.5 MSCI World monthly returns, Dec 1969 – Mar 2026

| | |
|---|---|
| **What** | 673 of 676 months transcribed from screenshots (index level + net return + rolling volatility) |
| **Where used** | The three pre-2005 eras (`MOVES_OIL` 1973-78, `MOVES_BLACKMON` 1987-89, `MOVES_DOTCOM` 2000-06) in all four current game files; master file `msci-world-master.csv` |
| **Already checked** | Every consecutive month's implied return (index ratio) matches the stated return within rounding, across all rows and batch seams; landmarks match the real record (1987-10 −17.00%, 2008-10 −18.96%, 2020-03 −13.23%, 1973-11 −12.97%, 1975-01 +14.58%) |
| **Still missing** | **3 months: Apr 1983, May 1983, Dec 1999** (fell between screenshots — not used by any current game feature, but the master file is incomplete). Supply screenshots of source rows 162–163 and 362 to close out. |
| **Verify** | Confirm which MSCI World variant this is (net TR, USD?) and spot-check the full series against the provider |

### 1.5a Online cross-check performed (July 2026) — passed

As a pre-verification sanity layer, calendar-year returns were compounded from
every embedded monthly series and compared against publicly published figures
(MSCI factsheets, index trackers, S&P/Bloomberg year-end figures). Results:

| Series | Years checked | Result |
|---|---|---|
| Derived S&P 500 TR (`EQ_2020`) | 2020–2025 | 2020 +18.40 exact; 2022/2023/2024 within 0.02pp; 2025 +17.73 vs ≈+17.7 ✓; **2021 +28.66 vs published +28.71 (Δ0.05pp — benchmark-decomposition rounding, immaterial)** |
| Bloomberg US Agg (`AGG_2020`) | 2020–2025 | 2020–2024 within 0.05pp (2023 exact); **2025 +7.52 vs published +7.30 (Δ0.22pp — transcribed Oct/Nov/Dec 2025 values (0.60/0.40/0.30) look like rounded placeholders in the source sheet; confirm these three months)** |
| MSCI World net USD (master CSV) | 1970–2025 spot years | 2008 −40.71 **exact**; 2024 +18.67 **exact**; 2020 +15.90 **exact**; 2022 −18.15 vs −18.14; 2023 +23.81 vs +23.79; 2025 +21.10 vs 21.09; Oct-1987 month −17.0 ✓; Oct-2008 month −18.9 ✓. (A 1990 figure of −16.5% found in one source appears to be the gross variant; ours −17.01 is consistent with the net series that matches every other year.) |
| 60/40 benchmark (`BENCH_0525`) | components | Equals 0.6·S&P + 0.4·Agg within 0.002pp over 2020–2025; Oct-2008 −11.02 consistent with published component months |
| All on-screen results | era endpoints, headline stat, clustering claim | Independently recomputed in Python from the raw series — **all six era hold/missed figures, $250,945/$135,882, and "6 of 10 best within 6 months of a worst" match exactly** |

This confirms the series are the genuine indices, but does **not** replace the
formal source verification below (public trackers are themselves secondary).

### 1.6 Modeling simplifications to bless (not errors — disclosed choices)

- **Cash yields a flat 2%/yr** when a player sells. Real cash yielded ~0% in
  2020–21 and ~5% in 2023–24. Fine for an educational POC; confirm acceptable.
- **Pre-2005 eras are 100% equity** (no verified bond data before 2005) while
  2005+ eras are 60/40 blends. Disclosed on-screen per era; confirm acceptable.
- **"Sat out the best months"** = same portfolio with that period's best months
  held in cash — an illustration of missing the market's best stretch, not a
  simulated trading strategy. Confirm framing acceptable.

---

## 2 · Compliance / brand review (blocking)

- [ ] **Branding**: Capital Group logo + name used throughout; "The Capital
  System" phrase appears in reveal cards. Confirm usage rights and framing.
- [ ] **Performance presentation**: all fund figures net-of-fees only (never
  gross); hypothetical/illustrative framing on every chart; past-performance
  language present. Review each edition's disclaimer text.
- [ ] **Sales edition specifics**: fund facts panel and standardized-returns
  table are now populated from publicly available fund information (Jul 2026,
  see §1.1) — confirm against the current prospectus/fact sheet and
  compliance-approve. The fund chart line is now drawn from the §1.1 rebuilt
  approximation (year-ends exact, monthly shape approximate, disclosed
  on-screen) — swap in the verified monthly net series and review the
  approximation disclosure before client use.
- [ ] **Public exposure (interim risk, accepted)**: the prototype is live at
  `https://cheesin30.github.io/decisionframework/` with a wide-open Firebase
  Realtime Database behind the live room (`.read/.write: true` on `/rooms`).
  **Decision (Jul 2026): keep up during testing; TAKE DOWN before the
  compliance review concludes.** Takedown = delete the repo's `gh-pages`
  branch + disable/lock the Firebase database rules.
- [ ] **Data collected**: live room stores self-chosen nicknames + votes only,
  in-memory / throwaway rooms. No emails, no accounts, no PII beyond nickname.
  Confirm this meets internal privacy bar for events.

---

## 3 · Deliverable & hosting decisions (recorded July 2026)

- **Primary deliverables**: ① Live Room edition (audience events),
  ② Learning edition (product-agnostic solo), ③ Sales edition (fund-included
  solo, gated on §1.1). The two earlier solo games (2005–2025 original,
  2020–2025) remain in the repo as reference/exploration, not maintained
  deliverables.
- **Event network reality**: audiences will be on **mixed/cellular** networks →
  the live room needs a **publicly reachable address**. Options: (a) current
  Firebase + static-host setup, or (b) the bundled relay
  (`live-server/server.js`) exposed through an IT-managed public endpoint.
  A fully internal server only works if the audience joins venue/corp WiFi.
- **No build-step consolidation for now**: the editions stay as standalone
  single files (POC posture); revisit if this becomes a maintained product.

## 4 · Sign-off

| Item | Owner | Date | Signed |
|---|---|---|---|
| §1.1 AMBAL net composite resolved | | | |
| §1.2–1.5 index series verified | | | |
| §1.6 modeling choices accepted | | | |
| §2 compliance/brand approved | | | |
| Public site taken down / blessed | | | |
