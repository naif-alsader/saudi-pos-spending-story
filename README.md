# Where Saudi Shoppers Are Heading

A data story on Saudi consumer card spending, May 2020 – July 2026, built from open data on the [KAPSARC Data Portal](https://data.kapsarc.org) (SAMA and GASTAT sources).

**Bottom line (v2):** in-store card spending has matured and now grows about as fast as household consumption (+6.3% nominal, +4.2% real). Online Mada payments are growing ~46% a year, but mostly by taking share from other payment methods. Buraidah's lead in city growth is robust; the apparent surge in clothing is largely a 2025 reclassification.

## Revised findings (v2, after critique and GDP cross-check)

| Topic | Finding |
|---|---|
| National | In-store card spending grew **+6.3%** (90% range 4.5–8.1%) in the 52 weeks to Feb 2026 vs a year earlier (Ramadan-aligned); **+4.2% after inflation**. |
| Consumption | In-store cards plateaued at ~32% of household consumption since 2022; card growth now tracks consumption (+5.8% vs +5.4% in 2025). |
| Online | Online Mada rose 128 bn SAR in 2025, more than all household consumption (+114 bn): a payment-method shift, not new demand. |
| Cities | Buraidah fastest (+10.8%, first in 97% of bootstrap resamples); Riyadh +8.6%; Tabouk +2.9%. City growth rankings are only moderately persistent (rank correlation 0.38 latest year). |
| Sectors | Like-for-like: gas +7.1%, food +5.2%, hotels +4.1%, restaurants +1.7%, health −5.4%. Clothing +7% to +18% (reclassified in Jul 2025). Jewelry +32% is all gold price (volume ≈ −12%). |

## Data

KAPSARC datasets are pulled with `fetch_data.py` (snapshots in `data/raw/`, all listed as Public Domain on the portal; sources: SAMA and GASTAT). CPI and gold series are in `data/external/` (see its README).

| Dataset (KAPSARC id) | Use |
|---|---|
| `point-of-sale-transactions-by-sector-and-city` | Weekly POS, 11 cities / 17 sectors, May 2020 – Jul 2025 |
| `detailed-point-of-sale-transactions-by-sector-and-city` | Weekly POS, 61 cities / 30 sectors, Jun 2025 – Mar 2026 |
| `pos-transactions` | Monthly POS and Mada e-commerce, to Jul 2026 |
| `household-income-and-consumption-expenditure-survey` | 2023 regional spending mix (IPF seed), household income |
| `saudi-arabia-population-by-administrative-region-nationality-and-sex` | 2024 population for per-capita spend |
| `real-estate-indices-by-regions-2023-100` | Regional property price change (entry-cost proxy) |
| `gross-domestic-product-by-expenditure-components-at-current-prices-2023-100` | Private final consumption benchmark |
| `gross-domestic-product-by-kind-of-economic-activity-at-current-prices-2023-100` | Trade, restaurants & hotels value added |
| `number-of-new-individual-proprietorships-by-region` | Business-formation proxy (2023) |
| `population-by-detailed-age-gender-governorate-nationality-and-region` | Census 2022 population by governorate |

## Methods

- **Ramadan-aligned windows.** Growth compares the 52 weeks ending the last full week before Ramadan with the same window a year earlier, so each holds one Ramadan and both Eids.
- **Linking series.** National and city totals match on the overlap weeks (29 Jun, 6 Jul 2025); `build.py` asserts this.
- **Sectors.** Food, restaurants (+ bakeries), hotels, gas and utilities match the old definitions exactly on the overlap weeks; health (medical + pharmacy) matches within 3%. Other sectors absorbed merchants from old "Other"/"Misc" and are spliced by their overlap ratio and flagged.
- **Uncertainty.** Paired moving-block bootstrap (block 4 weeks, 4,000 draws) gives 90% ranges and city ranking probabilities.
- **Real growth.** Deflated by GASTAT CPI (general index or matching division).
- **Raking.** Region × sector via iterative proportional fitting with three seeds (survey base, alternative mapping, no survey) to show sensitivity. Output: `outputs/raking_region_sector_bn.csv`.

## Reproduce

```bash
pip install -r requirements.txt
python check_freshness.py   # is there newer data on the portal?
python fetch_data.py        # optional: refresh data/raw
python src/build.py         # writes outputs/results.json (every number in the report)
```

## Caveats

Card-terminal and Mada data only (no cash, no non-Mada online cards); city = where the card is used (SAMA's assignment rule is undocumented); revenue, not profit; reclassified sectors rest on a two-week splice; raking tilts come only from the 2023 survey; no rents or competitor data. Not investment advice.
