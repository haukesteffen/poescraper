import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

'''
database: poeitems
table: items
'''

#explicit_mods = np.empty()
price_chaos_per_ex = 113.0

engine = create_engine('postgresql://xxx:xxx@localhost:5432/poeitems')
df=pd.read_sql_query('select * from items',con=engine)


'''subset_ex = df['price'].str.contains('exalted')
subset_c = df['price'].str.contains('chaos')
df = df[subset_c|subset_ex]
print(df.head())
subset_ex = df['price'].str.contains('exalted')
df['price'] = df['price'].str.replace('~price ','')
df['price'] = df['price'].str.replace(' exalted','')
df['price'] = df['price'].str.replace(' chaos','')
df['price'] = df['price'].str.replace('~b/o ','')
df['price'] = df['price'].replace('', np.nan)
df['price'] = df['price'].dropna()
df['price'] = df['price'].astype(float)
df['price'][subset_ex] = df['price'][subset_ex]*price_chaos_per_ex

df.sort_values(by='price', ascending=False, inplace=True)
df.drop_duplicates(subset='itemid', inplace=True)
df = df[df['price'] <= 700]

print(df['itemid'].iloc[2])

sns.set_theme(style="whitegrid")
sns.scatterplot(x='price', y='ilvl', alpha=0.5, hue='basetype', data=df)
plt.show()
'''
df['explicit_numbers_removed'] = ''.join([str(j) for j in df['explicit']])
print(df['explicit_numbers_removed'].iloc[-1].dtype)