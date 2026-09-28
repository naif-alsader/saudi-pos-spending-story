"""Build every figure used in the report into outputs/results.json (plus CSV tables).

Run from anywhere:  python src/build.py
Inputs:  data/raw/*.csv (KAPSARC snapshots, see fetch_data.py)
         data/external/*.csv (optional: CPI and gold series, see data/external/README.md)
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
EXT = os.path.join(ROOT, "data", "external")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

IND = "number_value_change_transactions"
VAL = "Value of Transactions (In Thousand SAR)"
CNT = "Number of Transactions (In Thousand)"
OVERLAP = pd.to_datetime(["2025-06-29", "2025-07-06"])  # weeks present in both weekly datasets
SPLIT = pd.Timestamp("2025-07-06")  # last week taken from the old series
N_BOOT, BLOCK, SEED = 4000, 4, 20260928

# Last full week (weeks start on Sunday) before Ramadan begins. A 52-week window ending there holds exactly one
# Ramadan, one Eid al-Fitr and one Eid al-Adha, so consecutive windows compare like with like (plan item 3).
PRE_RAMADAN = {2022: "2022-03-20", 2023: "2023-03-12", 2024: "2024-03-03", 2025: "2025-02-16", 2026: "2026-02-08"}
GROWTH_YEARS = [2023, 2024, 2025, 2026]

# New (detailed) city names -> old city names; every other new city belongs to the old "OTHER" bucket.
CITY_NEW_TO_OLD = {"Riyadh": "RIYADH", "Jeddah": "JEDDAH", "Dammam": "DAMMAM", "Makkah": "MAKKAH",
                   "Al-Madinah": "MADINA", "Al-Khubar": "KHOBAR", "Buraidah": "BURAIDAH", "Tabouk": "TABOUK",
                   "Hayel": "HAIL", "Abha": "ABHA"}
CITY_LABEL = {"RIYADH": "Riyadh", "JEDDAH": "Jeddah", "DAMMAM": "Dammam", "MAKKAH": "Makkah", "MADINA": "Madinah",
              "KHOBAR": "Khobar", "BURAIDAH": "Buraidah", "TABOUK": "Tabouk", "HAIL": "Hail", "ABHA": "Abha",
              "OTHER": "Other cities"}

# Sectors whose definition did not change (checked on the overlap weeks): old name, new components.
EXACT = {
    "Food & beverages": ("Beverage and Food", ["6.Food & Beverages"]),
    "Restaurants, cafes & bakeries": ("Restaurants & Café", ["3.Restaurants & Café", "4.Bakeries & Pastries"]),
    "Hotels": ("Hotels", ["5.Hotels"]),
    "Gas stations": ("Gas Stations", ["17.Gas Stations"]),
    "Public utilities": ("Public Utilities", ["16.Public Utilities & Services"]),
    "Health (medical & pharmacy)": ("Health", ["2.1.Medical Services", "2.2.Pharmacies & Medical Supplies"]),
}
# Sectors that absorbed merchants from the old "Other" / "Misc" buckets: not comparable across the break.
RECLASSIFIED = {
    "Clothing & apparel": ("Clothing and Footwear", ["7.Apparel, Clothing & Accessories"]),
    "Jewelry": ("Jewelry", ["13.Jewelry"]),
    "Furniture": ("Furniture", ["11.Furniture & Home Supplies"]),
    "Electronics": ("Electronic & Electric Devices", ["10.Electronic & Electric Devices"]),
    "Construction materials": ("Construction & Building Materials", ["12.Construction & Building Materials"]),
    "Recreation & culture": ("Recreation and Culture", ["8.Recreation & Culture"]),
    "Telecom": ("Telecommunication", ["14.Telecommunication"]),
    "Education": ("Education", ["15.Education"]),
    "Transportation": ("Transportation", ["1. Transportation"]),
}

REGIONS = ["Riyadh", "Makkah", "Madinah", "Eastern", "Qassim", "Asir", "Tabuk", "Hail", "Northern Borders",
           "Jazan", "Najran", "Al-Baha", "Al-Jouf"]
CITY_TO_REGION = {
    "Riyadh": ["Riyadh", "Al-Kharj", "Al-Dawadmi", "Al-Majma'a", "Al-Zulfi", "Al-Muzahmiya", "Wadil-Dawaser",
               "Afeef", "Shagraa", "Al-Queyah"],
    "Makkah": ["Makkah", "Jeddah", "Al-Tayef", "Al-Gunfudah", "Rabehg", "Al-laith"],
    "Madinah": ["Al-Madinah", "Yanbu", "Al-Ola", "Amluj"],
    "Eastern": ["Dammam", "Al-Khubar", "Al-Jubail", "Al-Hofuf", "Al-Mubarraz", "Hafrel-Batin", "Al-Qateef",
                "Al-Dahran", "Al-Khafji", "Saihat", "Safwa", "Al-Neairiyah"],
    "Qassim": ["Buraidah", "Onaizah", "Al-Rass", "Al-Bekairiyah", "Al-Badaea"],
    "Asir": ["Abha", "Khamis-Mushait", "Mahayel", "Besha", "Ahad-Rufaidah", "Ahad-Almasarha"],
    "Tabuk": ["Tabouk"], "Hail": ["Hayel"], "Northern Borders": ["Ar'ar", "Rafha"],
    "Jazan": ["Jazan", "Sabya", "Abu-Areesh", "Samta", "Baish", "Al-Darb"],
    "Najran": ["Najran", "Sharora"], "Al-Baha": ["Al-Baha"], "Al-Jouf": ["Sakaka", "Al-Qurayyat", "Tabarjal", "Tareef"],
}
C2R = {c: r for r, cs in CITY_TO_REGION.items() for c in cs}
REGION_NAMES = {  # canonical region -> name used in each source
    "hies": dict(zip(REGIONS, ["Riyadh", "Makkah", "Madinah", "Eastern Province", "Qassim", "Asir", "Tabuk", "Hail",
                               "Northern Border", "Jazan", "Najran", "Al-Baha", "Al-Jouf"])),
    "pop": dict(zip(REGIONS, ["Riyadh", "Makkah", "Al-Madinah", "Eastern Region", "Al-Qassim", "Asir", "Tabuk", "Hail",
                              "Northern Borders", "Jazan", "Najran", "Al-Bahah", "Al-Jawf"])),
    "realestate": dict(zip(REGIONS, ["Riyadh", "Makkah", "Madinah", "Eastern Province", "Al Qaseem", "Aseer", "Tabouk",
                                     "Hail", "Northern Borders", "Jazan", "Najran", "Al Baha", "Al Jouf"])),
    "prop": dict(zip(REGIONS, ["Riyadh", "Makkah", "Al-Madinah", "Eastern", "Al-Qassim", "Asir", "Tabuk", "Ha'il",
                               "Northern Borders", "Jazan", "Najran", "Al-Baha", "Al-Jawf"])),
}
GOV_LABEL = {"Ar Riyadh": "Riyadh", "Makkah Al Mukarramah": "Makkah", "Ad Dammam": "Dammam", "Al Madinah Al Munawwarah": "Madinah",
             "Al Taif": "Taif", "Buraydah": "Buraidah", "Al Khubar": "Khobar", "Khamis Mushayt": "Khamis Mushait",
             "Al Qatif": "Qatif", "Al Jubayl": "Jubail", "Hafar Al Batin": "Hafar Al-Batin", "Al Kharj": "Kharj",
             "Unayzah": "Unaizah", "Al Ahsa": "Al-Ahsa (Hofuf + Mubarraz)"}
# POS city -> census 2022 governorate, for spending per resident at city level (plan item 9).
CITY_TO_GOVERNORATE = {
    "Riyadh": "Ar Riyadh", "Jeddah": "Jeddah", "Makkah": "Makkah Al Mukarramah", "Dammam": "Ad Dammam",
    "Al-Madinah": "Al Madinah Al Munawwarah", "Al-Tayef": "Al Taif", "Buraidah": "Buraydah", "Al-Khubar": "Al Khubar",
    "Tabouk": "Tabuk", "Khamis-Mushait": "Khamis Mushayt", "Al-Qateef": "Al Qatif", "Al-Jubail": "Al Jubayl",
    "Hayel": "Hail", "Hafrel-Batin": "Hafar Al Batin", "Najran": "Najran", "Abha": "Abha", "Al-Kharj": "Al Kharj",
    "Yanbu": "Yanbu", "Sakaka": "Sakaka", "Jazan": "Jazan", "Onaizah": "Unayzah", "Al-Hofuf": "Al Ahsa",
    "Al-Mubarraz": "Al Ahsa",
}
# POS sector -> household-survey (COICOP) division used as the raking seed; three variants for sensitivity (item 10).
SEED_BASE = {
    "Transportation": "Transport", "Health": "Health", "Restaurants & Café": "Restaurants and accommodation services",
    "Bakeries & Pastries": "Food and beverages", "Hotels": "Restaurants and accommodation services",
    "Food & Beverages": "Food and beverages", "Apparel, Clothing & Accessories": "Clothing and footwear",
    "Recreation & Culture": "Recreation, sport and culture",
    "Professional & Business Services": "Personal care, social protection and miscellaneous goods and services",
    "Electronic & Electric Devices": "Furnishings, household equipment and routine household maintenance",
    "Furniture & Home Supplies": "Furnishings, household equipment and routine household maintenance",
    "Construction & Building Materials": "Housing, water, electricity, gas and other fuels",
    "Jewelry": "Personal care, social protection and miscellaneous goods and services",
    "Telecommunication": "Information and communication", "Education": "Education services",
    "Public Utilities & Services": "Housing, water, electricity, gas and other fuels", "Gas Stations": "Transport",
    "Laundry Services": "Personal care, social protection and miscellaneous goods and services", "Others": None,
}
SEED_ALT = {**SEED_BASE, "Electronic & Electric Devices": "Information and communication",
            "Jewelry": "Clothing and footwear",
            "Construction & Building Materials": "Furnishings, household equipment and routine household maintenance",
            "Bakeries & Pastries": "Restaurants and accommodation services"}


def read(name, **kw):
    return pd.read_csv(os.path.join(RAW, name + ".csv"), encoding="utf-8-sig", **kw)


def rnd(x, d=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


# ---------------------------------------------------------------- load
old = read("point-of-sale-transactions-by-sector-and-city", parse_dates=["starting_date"])
new = read("detailed-point-of-sale-transactions-by-sector-and-city", parse_dates=["starting_date"])
new["sectors"] = new.sectors.replace({"20.Total": "Total"})
R = {"as_of": {"weekly_pos_last_week": str(new.starting_date.max().date())}}


def weekly(df, measure, sectors=None, city="Total"):
    x = df[df[IND] == measure]
    x = x[x.city == city] if city is not None else x
    if sectors is not None:
        x = x[x.sectors.isin(sectors)]
    return x.groupby("starting_date").value.sum().sort_index()


def link(old_s, new_s):
    return pd.concat([old_s[old_s.index <= SPLIT], new_s[new_s.index > SPLIT]]).sort_index()


def splice(old_name, new_parts, measure=VAL):
    """Old-definition series extended with the new series rescaled by the overlap-week ratio."""
    o, n = weekly(old, measure, [old_name]), weekly(new, measure, new_parts)
    ratio = float((n.loc[OVERLAP] / o.loc[OVERLAP]).mean())
    return link(o, n / ratio), ratio


def window(s, year):
    end = pd.Timestamp(PRE_RAMADAN[year])
    w = s[(s.index > end - pd.Timedelta(weeks=52)) & (s.index <= end)]
    assert len(w) == 52, (year, len(w))
    return w.values


def boot_idx(rng):
    starts = rng.integers(0, 52 - BLOCK + 1, size=(N_BOOT, 52 // BLOCK))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(N_BOOT, -1)


def growth_ci(s, year, idx):
    """Growth of the pre-Ramadan window vs the previous one, with a paired moving-block bootstrap interval (item 7)."""
    a, b = window(s, year), window(s, year - 1)
    g = a.sum() / b.sum() - 1
    draws = a[idx].sum(1) / b[idx].sum(1) - 1
    return g * 100, np.percentile(draws, 5) * 100, np.percentile(draws, 95) * 100, draws


rng = np.random.default_rng(SEED)
IDX = boot_idx(rng)

# ---------------------------------------------------------------- national (items 2, 3, 7)
nat_v = link(weekly(old, VAL, ["Total"]), weekly(new, VAL, ["Total"]))
nat_n = link(weekly(old, CNT, ["Total"]), weekly(new, CNT, ["Total"]))
assert np.allclose(weekly(old, VAL, ["Total"]).loc[OVERLAP], weekly(new, VAL, ["Total"]).loc[OVERLAP], rtol=1e-5)

r52v, r52n = nat_v.rolling(52).sum(), nat_n.rolling(52).sum()
R["headline"] = {
    "definition": "rolling 52-week sum vs the previous 52 weeks, value of in-store card transactions",
    "last_week": str(nat_v.index[-1].date()),
    "value_growth_pct": rnd((r52v.iloc[-1] / r52v.iloc[-53] - 1) * 100),
    "count_growth_pct": rnd((r52n.iloc[-1] / r52n.iloc[-53] - 1) * 100),
    "value_52w_bn": rnd(r52v.iloc[-1] / 1e6),
}
q = pd.DataFrame({"v": r52v / r52v.shift(52) - 1, "n": r52n / r52n.shift(52) - 1}).dropna()
q = q.groupby(q.index.to_period("Q")).tail(1)
R["quarterly_growth"] = [{"q": f"{i.year} Q{i.quarter}", "value": rnd(r.v * 100), "count": rnd(r.n * 100)}
                         for i, r in q[q.index >= "2022-04-01"].iterrows()]
yr = pd.DataFrame({"v": nat_v, "n": nat_n})
ya = yr.groupby(yr.index.year).agg(v=("v", "sum"), n=("n", "sum"), wk=("v", "size"))
R["annual"] = [{"year": int(y), "weeks": int(r.wk), "avg_week_bn": rnd(r.v / r.wk / 1e6), "ticket_sar": rnd(r.v / r.n, 0),
                "total_bn": rnd(r.v / 1e6, 0)} for y, r in ya.iterrows()]
R["national_hijri"] = []
for y in GROWTH_YEARS:
    g, lo, hi, _ = growth_ci(nat_v, y, IDX)
    gn, _, _, _ = growth_ci(nat_n, y, IDX)
    R["national_hijri"].append({"window_end": PRE_RAMADAN[y], "value_growth": rnd(g), "lo": rnd(lo), "hi": rnd(hi),
                                "count_growth": rnd(gn)})

# ---------------------------------------------------------------- cities (items 3, 7, 15)
oc = old[(old[IND] == VAL) & (old.sectors == "Total") & (old.city != "Total")].pivot_table(
    index="starting_date", columns="city", values="value", aggfunc="sum")
nc = new[(new[IND] == VAL) & (new.sectors == "Total") & (new.city != "Total")].copy()
nc["old"] = nc.city.map(CITY_NEW_TO_OLD).fillna("OTHER")
nc = nc.pivot_table(index="starting_date", columns="old", values="value", aggfunc="sum")
assert np.allclose(oc.loc[OVERLAP].sort_index(axis=1), nc.loc[OVERLAP].sort_index(axis=1), rtol=1e-5)
city = pd.concat([oc[oc.index <= SPLIT], nc[nc.index > SPLIT]]).sort_index()
named = [c for c in CITY_LABEL if c != "OTHER"]
R["city_growth"] = {}
draws_by_city = {}
for c in list(CITY_LABEL):
    rows = []
    for y in GROWTH_YEARS:
        g, lo, hi, dr = growth_ci(city[c], y, IDX)
        rows.append({"window_end": PRE_RAMADAN[y], "growth": rnd(g), "lo": rnd(lo), "hi": rnd(hi)})
        if y == 2026:
            draws_by_city[c] = dr
    R["city_growth"][CITY_LABEL[c]] = rows
latest = pd.DataFrame({CITY_LABEL[c]: draws_by_city[c] for c in named})
first = latest.idxmax(axis=1).value_counts(normalize=True) * 100
top3 = latest.rank(axis=1, ascending=False).le(3).mean() * 100
R["city_rank_probability"] = {k: {"p_first": rnd(first.get(k, 0.0)), "p_top3": rnd(top3[k])} for k in latest.columns}
R["city_level_latest_window_bn"] = {CITY_LABEL[c]: rnd(window(city[c], 2026).sum() / 1e6) for c in CITY_LABEL}


def rank_persistence(frame):
    """Spearman correlation of growth ranks between consecutive windows, and whether last year's top 3 stay top 3."""
    out = []
    for y0, y1 in zip(GROWTH_YEARS[:-1], GROWTH_YEARS[1:]):
        g0 = frame.apply(lambda s: window(s, y0).sum() / window(s, y0 - 1).sum() - 1)
        g1 = frame.apply(lambda s: window(s, y1).sum() / window(s, y1 - 1).sum() - 1)
        top0 = set(g0.nlargest(3).index)
        out.append({"from": PRE_RAMADAN[y0], "to": PRE_RAMADAN[y1],
                    "spearman": rnd(g0.rank().corr(g1.rank()), 2),
                    "top3_kept": int(len(top0 & set(g1.nlargest(3).index))),
                    "top1_then": CITY_LABEL.get(g0.idxmax(), g0.idxmax()),
                    "top1_rank_next": int(g1.rank(ascending=False)[g0.idxmax()])})
    return out


R["city_rank_persistence"] = rank_persistence(city[named])

# ---------------------------------------------------------------- sectors (items 1 of critique / plan 6, 12)
sec, ratios = {}, {}
for label, (o_name, parts) in {**EXACT, **RECLASSIFIED}.items():
    sec[label], ratios[label] = splice(o_name, parts)
exact_old = [v[0] for v in EXACT.values()]
exact_new = [p for v in EXACT.values() for p in v[1]]
pool_old = weekly(old, VAL, ["Total"]) - weekly(old, VAL, exact_old)
pool_new = weekly(new, VAL, ["Total"]) - weekly(new, VAL, exact_new)
ratios["All reclassified sectors combined"] = float((pool_new.loc[OVERLAP] / pool_old.loc[OVERLAP]).mean())
sec["All reclassified sectors combined"] = link(pool_old, pool_new / ratios["All reclassified sectors combined"])
latest_bn = {}
for label, (o_name, parts) in {**EXACT, **RECLASSIFIED}.items():
    latest_bn[label] = weekly(new, VAL, parts)
latest_bn["All reclassified sectors combined"] = pool_new
R["sectors"] = []
for label, s in sec.items():
    g, lo, hi, _ = growth_ci(s, 2026, IDX)
    g25, lo25, hi25, _ = growth_ci(s, 2025, IDX)
    kind = "exact" if label in EXACT else ("pool" if label.startswith("All") else "reclassified")
    rec = {"sector": label, "kind": kind, "overlap_ratio": rnd(ratios[label], 3),
           "growth_2026": rnd(g), "lo_2026": rnd(lo), "hi_2026": rnd(hi), "growth_2025": rnd(g25),
           "level_new_def_bn": rnd(latest_bn[label][latest_bn[label].index > SPLIT].sum() / 1e6)}
    if kind == "reclassified":  # old-definition momentum: last 52 weeks available under the old definition
        o = weekly(old, VAL, [RECLASSIFIED[label][0]])
        rec["old_def_52w_to_jul2025"] = rnd((o.iloc[-52:].sum() / o.iloc[-104:-52].sum() - 1) * 100)
    R["sectors"].append(rec)
R["sector_level_weeks"] = int((weekly(new, VAL, ["Total"]).index > SPLIT).sum())
# like-for-like rank persistence on the old sector definitions (windows ending up to Feb 2025)
old_secs = old[(old[IND] == VAL) & (old.city == "Total") & (old.sectors != "Total")].pivot_table(
    index="starting_date", columns="sectors", values="value", aggfunc="sum")
sp = []
for y0, y1 in [(2023, 2024), (2024, 2025)]:
    g0 = old_secs.apply(lambda s: window(s, y0).sum() / window(s, y0 - 1).sum() - 1)
    g1 = old_secs.apply(lambda s: window(s, y1).sum() / window(s, y1 - 1).sum() - 1)
    sp.append({"from": PRE_RAMADAN[y0], "to": PRE_RAMADAN[y1], "spearman": rnd(g0.rank().corr(g1.rank()), 2),
               "top3_kept": int(len(set(g0.nlargest(3).index) & set(g1.nlargest(3).index))),
               "top3_then": list(g0.nlargest(3).index), "top3_next": list(g1.nlargest(3).index)})
R["sector_rank_persistence"] = sp

# ---------------------------------------------------------------- online vs consumption (items 1, 11)
p = read("pos-transactions", parse_dates=["date_object"])
pm = p[p.periodicity == "Monthly"].pivot_table(index="date_object", columns="indicator",
                                               values="value_in_different_units").sort_index()
mon = pm[["Total POS :  Sales (In Thousand Riyals)",
          "E-Commerce Transactions Using Mada Cards : Sales (In Thousand Riyals)"]].copy()
mon.columns = ["pos", "ecom"]
mon_n = pm[["Total POS :  Number of Transactions", "E-Commerce Transactions Using Mada Cards : Number of Transactions"]]
mon_n.columns = ["pos", "ecom"]
t12 = mon.rolling(12).sum()
R["online_trailing_12m"] = {"month": str(mon.index[-1].date())[:7],
                            "pos_bn": rnd(t12.pos.iloc[-1] / 1e6, 0), "ecom_bn": rnd(t12.ecom.iloc[-1] / 1e6, 0),
                            "pos_growth": rnd((t12.pos.iloc[-1] / t12.pos.iloc[-13] - 1) * 100),
                            "ecom_growth": rnd((t12.ecom.iloc[-1] / t12.ecom.iloc[-13] - 1) * 100),
                            "ecom_share_of_cards": rnd(t12.ecom.iloc[-1] / (t12.ecom.iloc[-1] + t12.pos.iloc[-1]) * 100)}
R["ecom_monthly_bn"] = {str(i.date())[:7]: rnd(v / 1e6) for i, v in mon.ecom.loc["2024-10-01":"2025-12-01"].items()}
ecom_ticket = (mon.ecom.groupby(mon.index.year).sum() * 1e3 / mon_n.ecom.groupby(mon.index.year).sum())  # counts are raw
pos_ticket = (mon.pos.groupby(mon.index.year).sum() * 1e3 / mon_n.pos.groupby(mon.index.year).sum())
R["online_semiannual"] = [{"m": str(i.date()), "pos": rnd(r.pos / 1e6, 0), "ecom": rnd(r.ecom / 1e6, 0)}
                          for i, r in t12.dropna()[t12.dropna().index.month.isin([1, 7])].iterrows()]
gx = read("gross-domestic-product-by-expenditure-components-at-current-prices-2023-100")
gx = gx[gx.unit == "Million of Saudi Riyals"].pivot_table(index="year", columns="expenditure_component",
                                                          values="gdp", aggfunc="sum")
pfce = gx["Gross Final Consumption Expenditure : Private Final Consumption Expenditure"] / 1e3
ga = read("gross-domestic-product-by-kind-of-economic-activity-at-current-prices-2023-100")
ga = ga[ga.unit == "Million of Saudi Riyals"].pivot_table(index="year", columns="economic_activity", values="gdp",
                                                          aggfunc="sum") / 1e3
trade_va = ga["Wholesale & Retail Trade, Restaurants & hotels"]
ann = mon.groupby(mon.index.year).sum() / 1e6
ann = ann[mon.groupby(mon.index.year).size() == 12]
cons = pd.DataFrame({"pfce": pfce, "pos": ann.pos, "ecom": ann.ecom, "trade_va": trade_va}).loc[2016:].dropna(
    subset=["pfce", "pos"])
R["consumption"] = [{"year": int(y), "pfce_bn": rnd(r.pfce, 0), "pos_bn": rnd(r.pos, 0), "ecom_bn": rnd(r.ecom, 0),
                     "pos_share": rnd(r.pos / r.pfce * 100), "all_share": rnd((r.pos + r.ecom) / r.pfce * 100),
                     "pfce_g": rnd((r.pfce / cons.pfce.get(y - 1, np.nan) - 1) * 100),
                     "pos_g": rnd((r.pos / cons.pos.get(y - 1, np.nan) - 1) * 100),
                     "ecom_g": rnd((r.ecom / cons.ecom.get(y - 1, np.nan) - 1) * 100) if y > 2019 else None,
                     "all_g": rnd(((r.pos + r.ecom) / (cons.pos + cons.ecom).get(y - 1, np.nan) - 1) * 100),
                     "trade_va_g": rnd((r.trade_va / cons.trade_va.get(y - 1, np.nan) - 1) * 100),
                     "ecom_avg_ticket_sar": rnd(ecom_ticket.get(y, np.nan), 0),
                     "pos_avg_ticket_sar": rnd(pos_ticket.get(y, np.nan), 0)}
                    for y, r in cons.iterrows()]
last = cons.index.max()
R["online_excess_over_consumption_bn"] = {
    "year": int(last), "ecom_increase_bn": rnd(cons.ecom[last] - cons.ecom[last - 1], 0),
    "pfce_increase_bn": rnd(cons.pfce[last] - cons.pfce[last - 1], 0),
    "pos_increase_bn": rnd(cons.pos[last] - cons.pos[last - 1], 0)}

# ---------------------------------------------------------------- location, supply-side proxies (items 9, 14)
L0 = new.starting_date > SPLIT
nweeks = int(new[L0].starting_date.nunique())
cn = new[L0 & (new[IND] == VAL) & (new.sectors == "Total") & (new.city != "Total")].groupby("city").value.sum()
gov = read("population-by-detailed-age-gender-governorate-nationality-and-region").groupby("governorate").population.sum()
per_res = {}
for c, gname in CITY_TO_GOVERNORATE.items():
    per_res.setdefault(gname, [0.0, c])
    per_res[gname][0] += cn.get(c, 0.0)
R["spend_per_resident"] = sorted([
    {"city": GOV_LABEL.get(g, g),
     "sar_per_resident_yr": rnd(v * 1e3 * 52 / nweeks / gov[g], 0), "population_2022": int(gov[g])}
    for g, (v, c) in per_res.items()], key=lambda d: -d["sar_per_resident_yr"])
R["spend_weeks"] = nweeks
rpop = read("saudi-arabia-population-by-administrative-region-nationality-and-sex")
rpop = rpop[(rpop.date == rpop.date.max()) & (rpop.gender == "Total")].set_index("region").value
reg_spend = cn.groupby(lambda c: C2R.get(c, "Unassigned")).sum()
hies = read("household-income-and-consumption-expenditure-survey")
inc = hies[(hies.indicator == "Average Household Monthly Disposable Income") & hies.region.notna()
           & hies.coicop_divisions.isna() & (hies.nationality_of_household_head == "Total")].groupby("region").value.first()
re_ = read("real-estate-indices-by-regions-2023-100")
re_last = re_[re_.measure == "YoY"].date.max()
re_ = re_[(re_.measure == "YoY") & (re_.date == re_last)].set_index("city").value
prop = read("number-of-new-individual-proprietorships-by-region")
prop_year = int(prop.date.max())
prop = prop[prop.date == prop_year].set_index("region").value
R["regions"] = []
for r in REGIONS:
    pop = rpop[REGION_NAMES["pop"][r]]
    R["regions"].append({
        "region": r, "card_share_pct": rnd(reg_spend.get(r, 0) / cn.sum() * 100),
        "pop_share_pct": rnd(pop / rpop.drop("Total").sum() * 100),
        "sar_per_person_yr": rnd(reg_spend.get(r, 0) * 1e3 * 52 / nweeks / pop, 0),
        "hh_income_sar_month_2023": rnd(inc.get(REGION_NAMES["hies"][r]), 0),
        "property_price_yoy": rnd(re_.get(REGION_NAMES["realestate"][r])),
        "new_proprietorships_per_1000": rnd(prop.get(REGION_NAMES["prop"][r]) / pop * 1000, 2)})
R["region_meta"] = {"unassigned_share_pct": rnd(reg_spend.get("Unassigned", 0) / cn.sum() * 100),
                    "property_quarter": re_last, "proprietorship_year": prop_year,
                    "population_year": int(read("saudi-arabia-population-by-administrative-region-nationality-and-sex").date.max())}

# ---------------------------------------------------------------- raking at region level with seed sensitivity (item 10)
top = new[L0 & (new[IND] == VAL) & (new.city == "Total") & new.sectors.str.match(r"^\d+\.\s?[A-Za-z]")
          & (new.sectors != "Total")].copy()
top["s"] = top.sectors.str.replace(r"^\d+\.\s?", "", regex=True)
cols = top.groupby("s").value.sum()
rows_ = reg_spend.drop("Unassigned", errors="ignore").reindex(REGIONS)
cols = cols * rows_.sum() / cols.sum()
H = hies[(hies.indicator == "Percentage of Household Monthly Final Monetary Consumption Expenditure")
         & hies.region.notna() & hies.coicop_divisions.notna() & (hies.nationality_of_household_head == "Total")]
H = H.pivot_table(index="region", columns="coicop_divisions", values="value")


def rake(seed_map):
    seed = np.ones((len(REGIONS), len(cols)))
    if seed_map is not None:
        for i, r in enumerate(REGIONS):
            for j, s in enumerate(cols.index):
                d = seed_map.get(s)
                seed[i, j] = H.loc[REGION_NAMES["hies"][r], d] if d else 1.0
    X = seed.copy()
    for _ in range(1000):
        X *= (rows_.values / X.sum(1))[:, None]
        X *= (cols.values / X.sum(0))[None, :]
        if np.abs(X.sum(1) / rows_.values - 1).max() < 1e-10:
            break
    return pd.DataFrame(X, index=REGIONS, columns=cols.index)


variants = {"base": rake(SEED_BASE), "alternative": rake(SEED_ALT), "no_survey": rake(None)}
lq = {k: v.div(v.sum(axis=0), axis=1).div(v.sum(axis=1) / v.values.sum(), axis=0) for k, v in variants.items()}
key_secs = ["Apparel, Clothing & Accessories", "Food & Beverages", "Restaurants & Café", "Health", "Jewelry",
            "Furniture & Home Supplies"]
R["raking"] = [{"region": r, "sector": s, "bn_base": rnd(variants["base"].loc[r, s] / 1e6, 2),
                "bn_min": rnd(min(v.loc[r, s] for v in variants.values()) / 1e6, 2),
                "bn_max": rnd(max(v.loc[r, s] for v in variants.values()) / 1e6, 2),
                "index_base": rnd(lq["base"].loc[r, s], 2), "index_alt": rnd(lq["alternative"].loc[r, s], 2)}
               for r in ["Riyadh", "Makkah", "Eastern", "Madinah", "Qassim", "Asir"] for s in key_secs]
pd.concat({k: v / 1e6 for k, v in variants.items()}).round(3).to_csv(os.path.join(OUT, "raking_region_sector_bn.csv"))

# ---------------------------------------------------------------- inflation and gold (items 8, 12), optional inputs
cpi_path, gold_path = os.path.join(EXT, "saudi_cpi_monthly.csv"), os.path.join(EXT, "gold_monthly.csv")
if os.path.exists(cpi_path):
    cpi = pd.read_csv(cpi_path)
    head = cpi[cpi.division.str.lower().str.contains("general|headline|all")].copy()
    head["month"] = pd.PeriodIndex(head.month, freq="M")
    head = head.set_index("month").yoy_pct.sort_index()
    for rec in R["national_hijri"]:
        end = pd.Timestamp(rec["window_end"]).to_period("M")
        months = pd.period_range(end - 11, end, freq="M")
        pi = head.reindex(months)
        if pi.notna().sum() >= 10:
            rec["cpi_yoy_avg"] = rnd(pi.mean())
            rec["real_value_growth"] = rnd(((1 + rec["value_growth"] / 100) / (1 + pi.mean() / 100) - 1) * 100)
    R["cpi_source_rows"] = int(len(cpi))
    cpi["month"] = pd.PeriodIndex(cpi.month, freq="M")
    div = cpi.pivot_table(index="month", columns="division", values="yoy_pct")
    sector_div = {"Food & beverages": "Food And Beverages", "Restaurants, cafes & bakeries": "Restaurants And Accommodation Services",
                  "Hotels": "Restaurants And Accommodation Services", "Gas stations": "Transport", "Health (medical & pharmacy)": "Health",
                  "Clothing & apparel": "Clothing And Footwear", "Furniture": "Furnishings, Household Equipment And Routine Household Maintenance",
                  "Electronics": "Furnishings, Household Equipment And Routine Household Maintenance",
                  "Jewelry": "Personal Care, Social Protection And Miscellaneous Goods And Services",
                  "Telecom": "Information And Communication", "Education": "Education Services",
                  "Recreation & culture": "Recreation, Sport And Culture", "Transportation": "Transport",
                  "Public utilities": "Housing, Water, Electricity, Gas And Other Fuels",
                  "All reclassified sectors combined": "General Index", "Construction materials": "General Index"}
    months26 = pd.period_range(pd.Timestamp(PRE_RAMADAN[2026]).to_period("M") - 11, periods=12, freq="M")
    for rec in R["sectors"]:
        pi = div[sector_div[rec["sector"]]].reindex(months26).mean()
        rec["price_yoy_2026"] = rnd(pi)
        rec["real_2026"] = rnd(((1 + rec["growth_2026"] / 100) / (1 + pi / 100) - 1) * 100)
if os.path.exists(gold_path):
    gold = pd.read_csv(gold_path)
    gold["month"] = pd.PeriodIndex(gold.month, freq="M")
    gold = gold.set_index("month").usd_oz.sort_index()
    jw = sec["Jewelry"]
    jm = jw.groupby(jw.index.to_period("M")).sum()
    wk = jw.groupby(jw.index.to_period("M")).size()
    jm = (jm / wk)  # average weekly spend per month, robust to 4- vs 5-week months
    both = pd.DataFrame({"jewelry": jm, "gold": gold}).dropna()
    yoy = both.pct_change(12).dropna() * 100
    R["gold_vs_jewelry"] = {"months": int(len(yoy)), "corr_yoy": rnd(yoy.corr().iloc[0, 1], 2),
                            "series": [{"m": str(i), "jewelry_yoy": rnd(r.jewelry), "gold_yoy": rnd(r.gold)}
                                       for i, r in yoy.iterrows()]}
    for y in (2025, 2026):  # same pre-Ramadan windows as the spending growth
        end = pd.Timestamp(PRE_RAMADAN[y]).to_period("M")
        cur, prev = pd.period_range(end - 11, end, freq="M"), pd.period_range(end - 23, end - 12, freq="M")
        gg = gold.reindex(cur).mean() / gold.reindex(prev).mean() - 1
        jg = next(r for r in R["sectors"] if r["sector"] == "Jewelry")["growth_%d" % y] / 100
        R["gold_vs_jewelry"]["window_%d" % y] = {"gold_price_growth": rnd(gg * 100), "jewelry_spend_growth": rnd(jg * 100),
                                                  "implied_volume_growth": rnd(((1 + jg) / (1 + gg) - 1) * 100)}
    xs = yoy.gold.values
    beta = np.polyfit(xs, yoy.jewelry.values, 1)
    R["gold_vs_jewelry"]["slope"] = rnd(beta[0], 2)
    R["gold_vs_jewelry"]["intercept"] = rnd(beta[1], 1)

with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(R, f, indent=1, ensure_ascii=False)
print("wrote outputs/results.json with keys:", ", ".join(R))
