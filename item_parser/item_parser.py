#!/usr/bin/env python3

import os
import re
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from joblib import Parallel, delayed

n_jobs = os.cpu_count()
price_chaos_per_ex = 113.0
price_pattern = re.compile("^~(?:b/o|price)\s([\d\.]+)\s(exalted|chaos)$")


def extract_price(price_string=None):
    temp1 = price_pattern.match(price_string)
    if temp1 is None:
        return np.nan
    elif temp1.group(2) == "exalted":
        return float(temp1.group(1)) * price_chaos_per_ex
    elif temp1.group(2) == "chaos":
        return float(temp1.group(1))


def strip_digits(input_string):
    return "".join([i for i in input_string if i.isalpha() or i == " "])


def strip_alpha(input_string):
    return "".join([i for i in input_string if i.isnumeric() or i == " " or i == "."])


def convert_rolls(input_string):
    if not str.split(input_string):
        return 1.0
    else:
        return [np.mean([float(roll) for roll in str.split(input_string)])]
        


def item_parser(input_item):
    item_dict = {}
    item_dict["itemid"] = input_item.loc["itemid"]
    item_dict["price"] = input_item.loc["price"]
    item_dict["basetype"] = input_item.loc["basetype"]
    item_dict["ilvl"] = input_item.loc["ilvl"]
    item_dict["corrupted"] = input_item.loc["corrupted"]
    item_dict["timestamp"] = input_item.loc["ts"]
    for affix_category in ["implicit", "explicit", "fracturedmods"]:
        if input_item[affix_category] is None:
            continue
        for mod in input_item.loc[affix_category]:
            affix = strip_digits(mod) + " (" + affix_category + ")"
            value = strip_alpha(mod)
            item_dict[affix] = convert_rolls(value)
    return item_dict


def main():
    global output_df
    # connect to database and query all items
    print("connecting to database...")
    try:
        with open(".env-postgres") as f:
            engine = create_engine(
                "postgresql://" + f.readlines()[0] + "@localhost:5432/poeitems"
            )
    except:
        username = os.environ["DBUSER"]
        password = os.environ["DBPASSWORD"]
        host = os.environ["DBHOST"]
        engine = create_engine(
            "postgresql://"
            + username.strip()
            + ":"
            + password.strip()
            + "@"
            + host.strip()
            + ":5432/poeitems"
        )

    print("fetching data...")
    input_df = pd.read_sql_query("SELECT * FROM items", con=engine)

    # remove unnecessary strings and drop items priced without number
    print("formatting price data...")
    input_df["price"] = input_df["price"].apply(extract_price)
    input_df.dropna(subset=["price"], inplace=True)

    # parse input dataframe into output dataframe
    print("parsing items into machine learnable form...")
    item_list = Parallel(n_jobs=n_jobs)(
        delayed(item_parser)(item) for _, item in input_df.iterrows()
    )
    output_df = pd.DataFrame(item_list).fillna(0.0).set_index("itemid")
    output_df = output_df.loc[output_df.index.drop_duplicates()]

    # load lexicon and merge dataframes
    lexicon = pd.read_pickle('data/lexicon.pkl')
    output_df = pd.concat([lexicon, output_df], join='outer')

    # save dataframe to csv file
    print("saving data as pickle...")
    output_df.to_pickle("data/output.pkl")
    return


if __name__ == "__main__":
    main()


###TODO
# load data in chunks to save memory
