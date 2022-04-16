#!/usr/bin/env python3

import os
import time
import re
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from joblib import Parallel, delayed

n_jobs = os.cpu_count()
n_items = 1000
price_chaos_per_ex = 113.0
price_pattern = re.compile("^~(?:b/o|price)\s([\d\.]+)\s(exalted|chaos)")


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
    return [np.mean([float(roll) for roll in str.split(input_string)])]


def create_lexicon(df, subset=None):
    if subset == None:
        raise ValueError("Define a subset to create lexicon on.")
    mod_dict = {"mod": [""]}
    mods_df = pd.DataFrame.from_dict(mod_dict)
    for _, item in df.iterrows():
        if item[subset] is not None:
            for mod in item[subset]:
                mod_no_digits = strip_digits(mod)
                if mod_no_digits not in mods_df.values:
                    mods_df.loc[len(mods_df.index)] = mod_no_digits
    mods_df["mod"].replace("", np.nan, inplace=True)
    mods_df.dropna(inplace=True)
    return [s + " (" + subset + ")" for s in mods_df["mod"].tolist()]


def item_parser(input_item):
    global output_df
    if input_item.loc["itemid"] in output_df["itemid"]:
        pass
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
    return pd.DataFrame.from_dict(item_dict)


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
    input_df = pd.read_sql_query("SELECT * FROM items LIMIT 1000", con=engine)

    # remove unnecessary strings and drop items priced without number
    print("formatting price data...")
    input_df["price"] = input_df["price"].apply(extract_price)
    input_df.dropna(subset=["price"], inplace=True)

    # create affix lexica
    print("creating implicit lexicon...")
    implicit_lexicon = create_lexicon(input_df, "implicit")
    print("creating explicit lexicon...")
    explicit_lexicon = create_lexicon(input_df, "explicit")
    print("creating fractured lexicon...")
    fracturedmods_lexicon = create_lexicon(input_df, "fracturedmods")

    # merge info and affix lexica
    print("merging lexica...")
    info_lexicon = ["itemid", "price", "basetype", "ilvl", "corrupted", "timestamp"]
    output_df = pd.DataFrame(
        columns=info_lexicon
        + explicit_lexicon
        + implicit_lexicon
        + fracturedmods_lexicon
    )

    # parse input dataframe into output dataframe
    print("parsing items into machine learnable form...")
    df_item = Parallel(n_jobs=n_jobs)(
        delayed(item_parser)(item) for _, item in input_df.iterrows()
    )
    output_df = pd.concat(df_item, axis=0).fillna(0.0)

    # save dataframe to csv file
    print("saving data to csv...")
    output_df.to_csv("output.csv")
    return


if __name__ == "__main__":
    i = 0
    while True:
        print("Iteration " + str(i))
        i += 1
        main()
        time.sleep(60)


###TODO
# load data in chunks to save memory