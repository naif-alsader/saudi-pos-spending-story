import pandas as pd, numpy as np, re, json
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RAW = 'data/raw/'
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
M='Value of Transactions (In Thousand SAR)'
o=pd.read_csv(RAW+'point-of-sale-transactions-by-sector-and-city.csv',encoding='utf-8-sig',parse_dates=['starting_date']); o=o[o.number_value_change_transactions==M]
d=pd.read_csv(RAW+'detailed-point-of-sale-transactions-by-sector-and-city.csv',encoding='utf-8-sig',parse_dates=['starting_date']); d=d[d.number_value_change_transactions==M]
d.loc[d.sectors=='20.Total','sectors']='Total'
# ---- 1. combined national series
ot=o[(o.city=='Total')&(o.sectors=='Total')].set_index('starting_date').value.sort_index()
dt=d[(d.city=='Total')&(d.sectors=='Total')].set_index('starting_date').value.sort_index()
T=pd.concat([ot,dt]).groupby(level=0).last().sort_index()
r52=T.rolling(52).sum(); r13=T.rolling(13).sum()
tr=pd.DataFrame({'52w_yoy':(r52/r52.shift(52)-1)*100,'13w_yoy':(r13/r13.shift(52)-1)*100}).dropna()
print("== national trend"); print(tr.iloc[::4].tail(16).round(1))
# ---- 2. sector mapping check on overlap weeks
top=d[(d.city=='Total')&d.sectors.str.match(r'^\d+\.\s?[A-Za-z]')&(d.sectors!='Total')].copy()
top['s']=top.sectors.str.replace(r'^\d+\.\s?','',regex=True)
mp={'Transportation':'Transportation','Health':'Health','Restaurants & Café':'Restaurants & Café','Hotels':'Hotels','Food & Beverages':'Beverage and Food','Bakeries & Pastries':'Beverage and Food','Apparel, Clothing & Accessories':'Clothing and Footwear','Recreation & Culture':'Recreation and Culture','Electronic & Electric Devices':'Electronic & Electric Devices','Furniture & Home Supplies':'Furniture','Construction & Building Materials':'Construction & Building Materials','Jewelry':'Jewelry','Telecommunication':'Telecommunication','Education':'Education','Public Utilities & Services':'Public Utilities','Gas Stations':'Gas Stations'}
top['old']=top.s.map(mp)
ov=[pd.Timestamp('2025-06-29'),pd.Timestamp('2025-07-06')]
n=top[top.starting_date.isin(ov)].groupby('old').value.sum(); ol=o[(o.city=='Total')&o.starting_date.isin(ov)].groupby('sectors').value.sum()
print("== new/old ratio on overlap weeks"); print((n/ol).dropna().round(3))
# sector YoY Jul25-Mar26 vs Jul24-Mar25 (comparable ones only)
w1=('2025-07-13','2026-03-22'); w0=('2024-07-14','2025-03-23')
cur=top[top.starting_date.between(*w1)].groupby('old').value.sum()
prev=o[(o.city=='Total')&o.starting_date.between(*w0)].groupby('sectors').value.sum()
rat=n/ol; sy=pd.DataFrame({'bn_Jul25_Mar26':cur/1e6,'raw_yoy%':(cur/prev-1)*100,'splice_ratio':rat,'adj_yoy%':(cur/(prev*rat)-1)*100}).dropna().sort_values('adj_yoy%')
print("== sector yoy"); print(sy.round(1))
print("Total yoy: %.1f"%((dt[w1[0]:w1[1]].sum()/ot[w0[0]:w0[1]].sum()-1)*100))
# ---- 3. city YoY (10 comparable cities)
cm={'Riyadh':'RIYADH','Jeddah':'JEDDAH','Dammam':'DAMMAM','Makkah':'MAKKAH','Al-Madinah':'MADINA','Al-Khubar':'KHOBAR','Buraidah':'BURAIDAH','Tabouk':'TABOUK','Hayel':'HAIL','Abha':'ABHA'}
dc=d[(d.sectors=='Total')&(d.city!='Total')].copy(); dc['old']=dc.city.map(cm).fillna('OTHER')
n=dc[dc.starting_date.isin(ov)].groupby('old').value.sum(); ol=o[(o.sectors=='Total')&o.starting_date.isin(ov)].groupby('city').value.sum()
cur=dc[dc.starting_date.between(*w1)].groupby('old').value.sum(); prev=o[(o.sectors=='Total')&o.starting_date.between(*w0)].groupby('city').value.sum()
cy=pd.DataFrame({'bn':cur/1e6,'yoy%':(cur/prev-1)*100,'ratio_ok':(n/ol).round(3)}).dropna().sort_values('yoy%',ascending=False)
print("== city yoy"); print(cy.round(1))
# fine cities: level + within-period momentum (last 13w vs first 13w, both non-Ramadan?) just level
fc=dc[dc.starting_date.between(*w1)].groupby('city').value.sum().sort_values(ascending=False)/1e6
print("== 61-city levels bn (Jul25-Mar26)"); print(fc.round(2).to_string())
