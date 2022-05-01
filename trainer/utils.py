import tensorflow as tf
import pandas as pd
import numpy as np
import os, re
from sqlalchemy import create_engine
from joblib import Parallel, delayed
from sklearn.model_selection import train_test_split

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
    return "".join([i for i in input_string if i.isalpha() or i == " " or i == "(" or i == ")"])


def strip_alpha(input_string):
    return "".join([i for i in input_string if i.isnumeric() or i == " " or i == "."])


def convert_rolls(input_string):
    if not str.split(input_string):
        return 1.0
    else:
        return np.mean([float(roll) for roll in str.split(input_string)])
    

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

def fetch(start_id=None, itembase='ring', make_machine_learnable=True, save_progress = True):
    if start_id is None:
        try:
            with open(f"assets/last_fetched_{itembase}.txt", "r") as f:
                start_id = f.read()
        except:
            start_id = 0
            
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
    input_df = pd.read_sql_query(f"SELECT * FROM items WHERE id >= {start_id} AND itembase = '{itembase}' AND price != '';", con=engine)
    

    # remove unnecessary strings and drop items priced without number
    print("formatting price data...")
    input_df["price"] = input_df["price"].apply(extract_price)
    input_df.dropna(subset=["price"], inplace=True)

    # check number of new items
    n_items = len(input_df.index)
    print(f"fetched {n_items} new {itembase} items...")
    if n_items < 32:
        print("too few items to train model. aborting...")
        return 1

    if make_machine_learnable:
        convert(input_df=input_df, itembase=itembase)
        if save_progress:
            # save last item id
            last_id = input_df.iloc[-1].loc['id']
            with open(f"assets/last_fetched_{itembase}.txt", "w") as f:
                f.write(str(last_id))
        
    return input_df

def convert(input_df, itembase): 
    output_df = parse(input_df)
    output_df = pd.concat(
            [output_df.drop(columns=["basetype"]), pd.get_dummies(output_df["basetype"])],
            axis=1,
        )
        
    # load lexicon
    try:
        lexicon = pd.read_pickle(f"assets/lexicon_{itembase}.pkl")
    except:
        print(f'no lexicon found. creating new {itembase} lexicon...')
        create_lexicon(itembase=itembase)
        lexicon = pd.read_pickle(f"assets/lexicon_{itembase}.pkl")
        print(f'created new lexicon. please retrain the model.')
        return 1

    # merge dataframes
    output_df = pd.concat([lexicon, output_df], join="outer")

    # verify fetched data
    if len(output_df.columns) != len(lexicon.columns):
        print('lexicon does not match, maybe some new mods were found.')
        print('updating lexicon...')
        create_lexicon(itembase=itembase)
        print('created new lexicon. please retrain the model.')
        return 1
        
    # save dataframe to csv file
    print("saving data as pickle...")
    output_df.to_pickle(f"assets/new_items_{itembase}.pkl")

    return output_df

def train_model(itembase='ring', save_model=True):
    df = (
        pd.read_pickle(f"assets/new_items_{itembase}.pkl")
        .drop(columns=["timestamp"])
    )
    df["corrupted"] = df["corrupted"].astype(float)

    X = df.drop(columns=["price"]).astype(float).to_numpy()
    y = df["price"].astype(float).to_numpy()

    model = tf.keras.models.load_model(f'assets/model_{itembase}')
    model.fit(X, y, epochs=3, batch_size=32)
    model.save(f"assets/model_{itembase}")

    # save last item id
    with open(f"assets/last_fetched_{itembase}.txt", "r") as f:
        with open(f"assets/last_trained_{itembase}.txt", "w") as g:
            g.write(str(f.read()))

def create_lexicon(itembase):
    input_df = fetch(start_id=0, itembase=itembase, make_machine_learnable=False)
    output_df = parse(input_df)
    output_df = pd.concat(
            [output_df.drop(columns=["basetype"]), pd.get_dummies(output_df["basetype"])],
            axis=1,
    )
    lexicon = pd.DataFrame(columns=output_df.columns)
    lexicon.to_pickle(f'assets/lexicon_{itembase}.pkl')

def parse(input_df):
    # parse input dataframe into output dataframe
    print("parsing items into machine learnable form...")
    item_list = Parallel(n_jobs=n_jobs)(
        delayed(item_parser)(item) for _, item in input_df.iterrows()
    )
    output_df = pd.DataFrame(item_list).fillna(0.0).set_index("itemid")
    output_df = output_df.loc[output_df.index.drop_duplicates()]
    return output_df

def create_new_model(itembase):
    df = (
        pd.read_pickle(f"assets/new_items_{itembase}.pkl")
        .drop(columns=["timestamp"])
    )
    df["corrupted"] = df["corrupted"].astype(float)
    X = df.drop(columns=['price']).astype(float).to_numpy()
    y = df["price"].astype(float).to_numpy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42
    )

    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        min_delta=0,
        patience=20,
        verbose=0,
        mode="auto",
        baseline=None,
        restore_best_weights=True,
    )
    
    lexicon = pd.read_pickle(f'assets/lexicon_{itembase}.pkl')
    n_features = len(lexicon.columns) - 2

    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.Dense(400, activation="relu", input_shape=(n_features,)))
    model.add(tf.keras.layers.Dense(400, activation="relu"))
    model.add(tf.keras.layers.Dense(400, activation="relu"))
    model.add(tf.keras.layers.Dense(1, activation="relu"))
    model.compile(optimizer="adam", loss="mae")
    model.fit(X_train, y_train, epochs=200, batch_size=32, validation_data=(X_test, y_test), callbacks=[early_stopping])
    model.save(f'assets/model_{itembase}')

    # save last item id
    with open(f"assets/last_fetched_{itembase}.txt", "r") as f:
        with open(f"assets/last_trained_{itembase}.txt", "w") as g:
            g.write(str(f.read()))