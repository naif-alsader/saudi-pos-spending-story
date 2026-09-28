"""Compare the newest period on the KAPSARC portal with the local snapshot, before any re-analysis."""
import json
import urllib.request

import pandas as pd

API = "https://data.kapsarc.org/api/explore/v2.1/catalog/datasets/{}/records?select=max({})%20as%20mx&limit=1"
CHECKS = [  # dataset id, date field
    ("detailed-point-of-sale-transactions-by-sector-and-city", "starting_date"),
    ("pos-transactions", "date_object"),
    ("gross-domestic-product-by-expenditure-components-at-current-prices-2023-100", "date"),
    ("real-estate-indices-by-regions-2023-100", "date"),
]

for ds, field in CHECKS:
    with urllib.request.urlopen(API.format(ds, field)) as r:
        remote = json.load(r)["results"][0]["mx"]
    local = pd.read_csv(f"data/raw/{ds}.csv", encoding="utf-8-sig", usecols=[field])[field].astype(str).max()
    n = min(len(str(local)), 10)  # compare at the precision of the local field (YYYY-MM or YYYY-MM-DD)
    flag = "NEWER DATA AVAILABLE" if str(remote)[:n] > str(local)[:n] else "up to date"
    print(f"{ds[:60]:60s} local {str(local)[:10]}  portal {str(remote)[:10]}  {flag}")
