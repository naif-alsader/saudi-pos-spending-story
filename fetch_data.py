"""Download every KAPSARC dataset used in the analysis into data/raw/."""
import os, urllib.request
import pandas as pd

BASE = "https://data.kapsarc.org/api/explore/v2.1/catalog/datasets/{}/exports/csv?delimiter=,"
DATASETS = [
    "point-of-sale-transactions-by-sector-and-city",           # SAMA weekly POS, May 2020 - Jul 2025
    "detailed-point-of-sale-transactions-by-sector-and-city",  # SAMA weekly POS, Jun 2025 onwards, 61 cities
    "pos-transactions",                                        # SAMA monthly POS + Mada e-commerce
    "household-income-and-consumption-expenditure-survey",     # GASTAT HIES 2023
    "saudi-arabia-population-by-administrative-region-nationality-and-sex",
    "real-estate-indices-by-regions-2023-100",
    "gross-domestic-product-by-expenditure-components-at-current-prices-2023-100",   # GASTAT national accounts
    "gross-domestic-product-by-kind-of-economic-activity-at-current-prices-2023-100",
    "number-of-new-individual-proprietorships-by-region",
    "population-by-detailed-age-gender-governorate-nationality-and-region",          # census 2022 by governorate
]

os.makedirs("data/raw", exist_ok=True)
for ds in DATASETS:
    path = f"data/raw/{ds}.csv"
    print("downloading", ds)
    urllib.request.urlretrieve(BASE.format(ds), path)
    if ds.startswith("saudi-arabia-population"):  # drop the huge geo_shape column
        pd.read_csv(path, encoding="utf-8-sig", usecols=["date", "region", "gender", "value"]).to_csv(path, index=False)
    if ds.startswith("population-by-detailed"):  # keep one row per governorate
        g = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
        g.groupby(["region", "governorate"], as_index=False).population.sum().to_csv(path, index=False)
