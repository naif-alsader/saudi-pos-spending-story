import pandas as pd, numpy as np
import os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RAW = 'data/raw/'
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_columns',30)
# ---- e-commerce vs POS (monthly)
p=pd.read_csv(RAW+'pos-transactions.csv',encoding='utf-8-sig',parse_dates=['date_object'])
pm=p[p.periodicity=='Monthly'].pivot_table(index='date_object',columns='indicator',values='value_in_different_units').sort_index()
k={'Total POS :  Sales (In Thousand Riyals)':'POS','E-Commerce Transactions Using Mada Cards : Sales (In Thousand Riyals)':'Ecom'}
x=pm[list(k)].rename(columns=k).dropna(); x12=x.rolling(12).sum()
e=pd.DataFrame({'POS_12m_bn':x12.POS/1e6,'Ecom_12m_bn':x12.Ecom/1e6,'POS_yoy':(x12.POS/x12.POS.shift(12)-1)*100,'Ecom_yoy':(x12.Ecom/x12.Ecom.shift(12)-1)*100,'ecom_share%':x12.Ecom/(x12.Ecom+x12.POS)*100}).dropna()
print("== ecommerce"); print(e.iloc[::6].tail(10).round(1)); print(e.tail(1).round(1)); print("last month:",x.index.max())
# ---- IPF city x sector
M='Value of Transactions (In Thousand SAR)'
d=pd.read_csv(RAW+'detailed-point-of-sale-transactions-by-sector-and-city.csv',encoding='utf-8-sig',parse_dates=['starting_date']); d=d[(d.number_value_change_transactions==M)&d.starting_date.between('2025-07-13','2026-03-22')]
d.loc[d.sectors=='20.Total','sectors']='Total'
rows=d[(d.sectors=='Total')&(d.city!='Total')].groupby('city').value.sum()
top=d[(d.city=='Total')&d.sectors.str.match(r'^\d+\.\s?[A-Za-z]')&(d.sectors!='Total')].copy(); top['s']=top.sectors.str.replace(r'^\d+\.\s?','',regex=True)
cols=top.groupby('s').value.sum()
print("sector sum / city sum: %.3f"%(cols.sum()/rows.sum()))
cols=cols*rows.sum()/cols.sum()
reg={'Riyadh':['Riyadh','Al-Kharj','Al-Dawadmi','Al-Majma\'a','Al-Zulfi','Al-Muzahmiya','Wadil-Dawaser','Afeef','Shagraa','Al-Queyah'],
'Makkah':['Makkah','Jeddah','Al-Tayef','Al-Gunfudah','Rabehg','Al-laith'],
'Madinah':['Al-Madinah','Yanbu','Al-Ola','Amluj','Badr'],
'Eastern Province':['Dammam','Al-Khubar','Al-Jubail','Al-Hofuf','Al-Mubarraz','Hafrel-Batin','Al-Qateef','Al-Dahran','Al-Khafji','Saihat','Safwa','Al-Neairiyah'],
'Qassim':['Buraidah','Onaizah','Al-Rass','Al-Bekairiyah','Al-Badaea'],
'Asir':['Abha','Khamis-Mushait','Mahayel','Besha','Ahad-Rufaidah','Ahad-Almasarha'],
'Tabuk':['Tabouk'],'Hail':['Hayel'],'Northern Border':['Ar\'ar','Rafha'],'Jazan':['Jazan','Sabya','Abu-Areesh','Samta','Baish','Al-Darb'],
'Najran':['Najran','Sharora'],'Al-Baha':['Al-Baha'],'Al-Jouf':['Sakaka','Al-Qurayyat','Tabarjal','Tareef']}
c2r={c:r for r,cs in reg.items() for c in cs}
miss=[c for c in rows.index if c not in c2r and c!='Others']; print("unmapped:",miss)
h=pd.read_csv(RAW+'household-income-and-consumption-expenditure-survey.csv',encoding='utf-8-sig')
h=h[(h.indicator=='Percentage of Household Monthly Final Monetary Consumption Expenditure')&h.region.notna()&h.coicop_divisions.notna()&(h.nationality_of_household_head=='Total')]
H=h.pivot_table(index='region',columns='coicop_divisions',values='value'); H.loc['Total']=H.mean() if 'Total' not in H.index else H.loc['Total']; print('HIES regions:',list(H.index))
s2c={'Transportation':'Transport','Health':'Health','Restaurants & Café':'Restaurants and accommodation services','Bakeries & Pastries':'Food and beverages','Hotels':'Restaurants and accommodation services','Food & Beverages':'Food and beverages','Apparel, Clothing & Accessories':'Clothing and footwear','Recreation & Culture':'Recreation, sport and culture','Professional & Business Services':'Personal care, social protection and miscellaneous goods and services','Electronic & Electric Devices':'Furnishings, household equipment and routine household maintenance','Furniture & Home Supplies':'Furnishings, household equipment and routine household maintenance','Construction & Building Materials':'Housing, water, electricity, gas and other fuels','Jewelry':'Personal care, social protection and miscellaneous goods and services','Telecommunication':'Information and communication','Education':'Education services','Public Utilities & Services':'Housing, water, electricity, gas and other fuels','Gas Stations':'Transport','Laundry Services':'Personal care, social protection and miscellaneous goods and services','Others':None}
print("unmapped sectors:",[s for s in cols.index if s not in s2c])
seed=pd.DataFrame(index=rows.index,columns=cols.index,dtype=float)
for c in rows.index:
  r=c2r.get(c,'Total'); 
  for s in cols.index:
    cc=s2c.get(s); seed.loc[c,s]=H.loc[r,cc] if cc else 1.0
seed=seed.fillna(1.0)
X=seed.values.copy()
for it in range(500):
  X*= (rows.values/X.sum(1))[:,None]; X*= (cols.values/X.sum(0))[None,:]
  if np.abs(X.sum(1)/rows.values-1).max()<1e-9: break
E=pd.DataFrame(X,index=rows.index,columns=cols.index)/1e6
E.to_csv('outputs/est_city_sector_bn.csv')
print("IPF iters",it)
# location quotient: city share of sector vs city share of total
LQ=(E.div(E.sum(0),axis=1)).div(E.sum(1)/E.values.sum(),axis=0)
print("== estimated bn SAR Jul25-Mar26, top cities x key sectors")
key=['Apparel, Clothing & Accessories','Food & Beverages','Restaurants & Café','Health','Jewelry','Furniture & Home Supplies']
print(E.loc[['Riyadh','Jeddah','Dammam','Makkah','Al-Madinah','Al-Khubar','Buraidah','Al-Tayef','Khamis-Mushait','Tabouk','Hayel','Abha'],key].round(2))
print("== LQ (>1 = over-indexed vs national mix)"); print(LQ.loc[['Riyadh','Jeddah','Dammam','Makkah','Al-Madinah','Buraidah','Khamis-Mushait','Hayel'],key].round(2))
# ---- per-capita by region
pop=pd.read_csv(RAW+'saudi-arabia-population-by-administrative-region-nationality-and-sex.csv',encoding='utf-8-sig'); pop=pop[(pop.date==2024)&(pop.gender=='Total')].set_index('region').value
pr={'Riyadh':'Riyadh','Makkah':'Makkah','Madinah':'Al-Madinah','Eastern Province':'Eastern Region','Qassim':'Al-Qassim','Asir':'Asir','Tabuk':'Tabuk','Hail':'Hail','Northern Border':'Northern Borders','Jazan':'Jazan','Najran':'Najran','Al-Baha':'Al-Bahah','Al-Jouf':'Al-Jawf'}
print("pop regions:",list(pop.index))
rs=rows.groupby(lambda c:c2r.get(c,'Others')).sum()
pc=pd.DataFrame({'card_bn_38wk':rs/1e6}); pc['pop_m']=[pop.get(pr.get(r,''),np.nan)/1e6 for r in pc.index]; pc['SAR_per_person_annualised']=pc.card_bn_38wk*1e9/(pc.pop_m*1e6)*52/37
# household income / spend by region
inc=pd.read_csv(RAW+'household-income-and-consumption-expenditure-survey.csv',encoding='utf-8-sig')
ii=inc[(inc.indicator=='Average Household Monthly Disposable Income')&inc.region.notna()&inc.coicop_divisions.isna()&(inc.nationality_of_household_head=='Total')].groupby('region').value.first()
pc['hh_income_SAR_mo_2023']=ii
re_=pd.read_csv(RAW+'real-estate-indices-by-regions-2023-100.csv',encoding='utf-8-sig'); re_=re_[(re_.measure=='YoY')&(re_.date=='2026-03')].set_index('city').value
rr={'Riyadh':'Riyadh','Makkah':'Makkah','Madinah':'Madinah','Eastern Province':'Eastern Province','Qassim':'Al Qaseem','Asir':'Aseer','Tabuk':'Tabouk','Hail':'Hail','Northern Border':'Northern Borders','Jazan':'Jazan','Najran':'Najran','Al-Baha':'Al Baha','Al-Jouf':'Al Jouf'}
pc['realestate_yoy_Q1_26']=[re_.get(rr.get(r,''),np.nan) for r in pc.index]
print("== region proxies"); print(pc.sort_values('SAR_per_person_annualised',ascending=False).round(1))
