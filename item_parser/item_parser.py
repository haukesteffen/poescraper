#!/usr/bin/env python3

import os
import time
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from joblib import Parallel, delayed

n_jobs = os.cpu_count()
n_items = 1000
price_chaos_per_ex = 113.0

def strip_digits(input_string):
    return ''.join([i for i in input_string if i.isalpha() or i==' '])

def strip_alpha(input_string):
    return ''.join([i for i in input_string if i.isnumeric() or i==' ' or i=='.'])

def convert_rolls(input_string):
    return [np.mean([float(roll) for roll in str.split(input_string)])]

def create_lexicon(df, subset=None):
    if subset==None:
        raise ValueError('Define a subset to create lexicon on.')
    mod_dict = {'mod':['']}
    mods_df = pd.DataFrame.from_dict(mod_dict)
    for _, item in df.iterrows():
        if item[subset] is not None:
            for mod in item[subset]:
                mod_no_digits = strip_digits(mod)
                if mod_no_digits not in mods_df.values:
                    mods_df.loc[len(mods_df.index)] = mod_no_digits
    mods_df['mod'].replace('',np.nan, inplace=True)
    mods_df.dropna(inplace=True)
    return [s + ' (' + subset + ')' for s in mods_df['mod'].tolist()]

def item_parser(input_item):
    global output_df
    if input_item.loc['itemid'] in output_df['itemid']:
        pass
    item_dict = {}
    item_dict['itemid'] = input_item.loc['itemid']
    item_dict['price'] = input_item.loc['price']
    item_dict['basetype'] = input_item.loc['basetype']
    item_dict['ilvl'] = input_item.loc['ilvl']
    item_dict['corrupted'] = input_item.loc['corrupted']
    item_dict['timestamp'] = input_item.loc['ts']
    for affix_category in ['implicit', 'explicit', 'fracturedmods']:
        if input_item[affix_category] is None:
            continue
        for mod in input_item.loc[affix_category]:
            affix = strip_digits(mod) + ' ('+affix_category+')'
            value = strip_alpha(mod)
            item_dict[affix] = convert_rolls(value)
    return pd.DataFrame.from_dict(item_dict)


def main():
    global output_df
    #connect to database and query all items
    try:
        with open('.env-postgres') as f:
            engine = create_engine('postgresql://' + f.readlines()[0] + '@localhost:5432/poeitems')
    except:
        username = os.environ['DBUSER']
        password = os.environ['DBPASSWORD']
        host = os.environ['DBHOST']
        engine = create_engine('postgresql://' + username + ':' + password + '@' + host.strip() + ':5432/poeitems')
    input_df = pd.read_sql_query('SELECT * FROM items ORDER BY RANDOM() LIMIT ' + str(n_items), con=engine)

    #drop unidentified and unpriced items
    input_df.dropna(subset='explicit', axis='rows', inplace=True)
    subset_ex = input_df['price'].str.contains('exalted')
    subset_c = input_df['price'].str.contains('chaos')
    input_df = input_df[subset_c|subset_ex]

    #remove unnecessary strings and drop items priced without number
    subset_ex = input_df['price'].str.contains('exalted')
    input_df['price'] = input_df['price'].str.replace(' exalted','')
    input_df['price'] = input_df['price'].str.replace('~price ','')
    input_df['price'] = input_df['price'].str.replace(' chaos','')
    input_df['price'] = input_df['price'].str.replace('~b/o ','')
    input_df['price'] = input_df['price'].replace('', np.nan)
    input_df['price'] = input_df['price'].dropna()

    #convert to chaos and save as float
    input_df['price'] = input_df['price'].astype(float)
    input_df.loc[subset_ex, 'price'] = input_df.loc[subset_ex, 'price']*price_chaos_per_ex
    input_df = input_df[input_df['price'] > 0.1]

    #create affix lexica
    implicit_lexicon = create_lexicon(input_df, 'implicit')
    explicit_lexicon = create_lexicon(input_df, 'explicit')
    fracturedmods_lexicon = create_lexicon(input_df, 'fracturedmods')

    #merge info and affix lexica
    info_lexicon = ['itemid', 'price', 'basetype', 'ilvl', 'corrupted', 'timestamp']
    output_df = pd.DataFrame(columns=info_lexicon + explicit_lexicon + implicit_lexicon + fracturedmods_lexicon)

    #parse input dataframe into output dataframe
    df_item = Parallel(n_jobs=n_jobs)(delayed(item_parser)(item) for _, item in input_df.iterrows())
    output_df = pd.concat(df_item, axis=0).fillna(0.0)

    #save dataframe to csv file
    output_df.to_csv('output.csv')
    return


if __name__ == "__main__":
    i = 0
    while True:
        print('Iteration ' + str(i))
        i += 1
        main()
        time.sleep(20)


###TODO
#load data in chunks to save memory
#use regex for price filtering