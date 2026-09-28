# Where Saudi Shoppers Are Heading

A data story on Saudi consumer card spending, May 2020 – July 2026, built from open data on the [KAPSARC Data Portal](https://data.kapsarc.org) (SAMA and GASTAT sources).

**Bottom line:** in-store card spending has matured (growth fell from ~20% to ~5% a year), but online Mada spending is growing ~46% a year and is now ~35% of Mada spend. Buraidah has overtaken Riyadh as the fastest-growing major city, and clothing & apparel is the strongest large sector.

## The story in six acts

| Act | Finding |
|---|---|
| 1. The boom | Weekly in-store card spend rose from 7.6 bn SAR (2020) to 13.6 bn SAR (2025); 705 bn SAR in 2025. The average payment halved, 119 → 61 SAR. |
| 2. The slowdown | Rolling 52-week growth fell from +20% (2022) to +4–6% (late 2025 – Mar 2026). |
| 3. The plot twist | 12 months to Jul 2026: online Mada 387 bn SAR (+46%) vs in-store 732 bn SAR (+6%). |
| 4. The map | Jul 2025 – Mar 2026 vs a year earlier: Buraidah +9.7%, Madinah +6.9%, Riyadh +5.2% (was +11%), Dammam +3.0%, Tabouk +0.2%. |
| 5. The shelves | Clothing +24%, food & beverages +8%; furniture, electronics, recreation shrinking (splice-adjusted, indicative). |
| 6. Filling the gap | City × sector spending estimated with iterative proportional fitting (raking). |

## Data

All pulled with `fetch_data.py` (snapshots included in `data/raw/`):

| Dataset (KAPSARC id) | Use |
|---|---|
| `point-of-sale-transactions-by-sector-and-city` | Weekly POS, 11 cities / 17 sectors, May 2020 – Jul 2025 |
| `detailed-point-of-sale-transactions-by-sector-and-city` | Weekly POS, 61 cities / 30 sectors, Jun 2025 – Mar 2026 |
| `pos-transactions` | Monthly POS and Mada e-commerce, to Jul 2026 |
| `household-income-and-consumption-expenditure-survey` | 2023 regional spending mix (IPF seed), household income |
| `saudi-arabia-population-by-administrative-region-nationality-and-sex` | 2024 population for per-capita spend |
| `real-estate-indices-by-regions-2023-100` | Regional property price change (entry-cost proxy) |

## Methods

- **Linking series.** The old and detailed weekly datasets match exactly on the overlapping weeks (29 Jun and 6 Jul 2025), so national and city totals are concatenated directly.
- **Sector splice.** SAMA redefined sector categories in the detailed dataset. Growth is adjusted by the new/old ratio on the two overlap weeks — indicative only.
- **Seasonality.** Growth uses rolling 52-week sums or same-week-last-year comparisons so Ramadan and Eid shifts wash out.
- **City × sector (IPF / raking).** Seed = each region's household spending share by COICOP division (HIES 2023), mapped to POS sectors; rows are raked to actual city totals and columns to actual national sector totals until both match. Output: `outputs/est_city_sector_bn.csv`. Within-cell splits are modelled, not observed.

## Reproduce

```bash
pip install -r requirements.txt
python fetch_data.py                   # optional: refresh data/raw
python src/01_trend_city_sector.py     # national trend, sector and city growth
python src/02_ecommerce_ipf_proxies.py # e-commerce, IPF estimate, regional proxies
```

## Caveats

Card-terminal and Mada data only (no cash, no non-Mada online cards); revenue, not profit; the sector splice rests on two overlap weeks; the IPF split depends on the 2023 survey's regional patterns. Not investment advice.
