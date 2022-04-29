import tensorflow as tf
import pandas as pd
import numpy as np
import os, re
from sqlalchemy import create_engine
from joblib import Parallel, delayed
from sklearn.model_selection import RandomizedSearchCV, train_test_split


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
    #eturn "".join([i for i in input_string if i.isalpha() or i == " "])

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


def fetch():
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
    lexicon = pd.read_pickle("data/lexicon.pkl")
    output_df = pd.concat([lexicon, output_df], join="outer")

    # save dataframe to csv file
    print("saving data as pickle...")
    output_df.to_pickle("data/output.pkl")
    return


def convert_input(item_paste):
    item_dict = {}
    lexicon = pd.read_pickle('data/lexicon.pkl')
    for line in item_paste.split('\n'):
        if " (crafted)" in line:
            line = line.replace(' (crafted)','')
        if "(implicit)" in line:
            affix = strip_digits(line)
            value = strip_alpha(line)
            item_dict[affix] = convert_rolls(value)
        if "(fractured)" in line:
            affix = strip_digits(line).replace('fractured', 'fracturedmods')
            value = strip_alpha(line)
            item_dict[affix] = convert_rolls(value)
        if "Item Level" in line:
            item_dict['ilvl'] = convert_rolls(strip_alpha(line))
        if strip_digits(line) + ' (explicit)' in lexicon.columns:
            affix = strip_digits(line) + " (explicit)"
            value = strip_alpha(line)
            item_dict[affix] = convert_rolls(value)
    item_dict['basetype'] = item_paste.split('\n')[3]
    if 'Synthesised ' in item_dict["basetype"]:
        item_dict['basetype'] = item_dict['basetype'].replace('Synthesised ','')
    return item_dict


def convert_dict_to_item_df(input_dict):
    lexicon = pd.read_pickle('data/lexicon.pkl')
    input_df = pd.DataFrame(input_dict, index=[0])
    item_df = pd.concat([lexicon, input_df], join='outer')
    item_df.fillna(0.0, inplace=True)
    item_df.set_index('itemid')
    basetype = item_df["basetype"]
    item_df[basetype] = 1.0
    return item_df


def estimate_price(input_item_df):
    model = tf.keras.models.load_model('data/model')
    input_item_df.set_index('itemid', inplace=True)
    X = input_item_df.drop(columns=["basetype"]).astype(float).to_numpy()
    #y = input_item_df["price"].astype(float).to_numpy()
    return model.predict_on_batch(X)


def train_model(df, save_model=True):
    df = (
        pd.read_pickle("data/output.pkl")
        .set_index("itemid")
        .drop(columns=["timestamp"])
    )
    df["corrupted"] = df["corrupted"].astype(float)

    X = (
        pd.concat(
            [df.drop(columns=["price", "basetype"]), pd.get_dummies(df["basetype"])],
            axis=1,
        )
        .astype(float)
        .to_numpy()
    )
    y = df["price"].astype(float).to_numpy()

    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=0.2, random_state=42
    )

    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        min_delta=0,
        patience=10,
        verbose=0,
        mode="auto",
        baseline=None,
        restore_best_weights=True,
    )

    def create_model(n_neurons=300, n_layers=3):
        model = tf.keras.models.Sequential()
        for _ in range(n_layers):
            model.add(tf.keras.layers.Dense(n_neurons, activation='relu'))
        model.add(tf.keras.layers.Dense(1))
        model.compile(optimizer="adam", loss="mae")
        return model

    '''model = tf.keras.wrappers.scikit_learn.KerasRegressor(build_fn=create_model, epochs=20, batch_size=32, validation_data=(X_val, y_val), callbacks=[early_stopping])
    params = {
        'n_neurons':[600],
        'n_layers':[1, 2, 3],
    }
    random_search = RandomizedSearchCV(model, param_distributions=params, cv=3)
    random_search_results = random_search.fit(X_train, y_train)
    print(f'best score: {random_search_results.best_score_}')
    print(f'best params: {random_search_results.best_params_}')'''

    '''nns = [300, 400, 500]
    nls = [2, 3, 4]
    model_dict = {
        'n_neurons':[],
        'n_layers':[],
        'loss':[],
    }
    for nn in nns:
        for nl in nls:
            model = create_model(n_neurons=nn, n_layers=nl)
            model.fit(
                X_train,
                y_train,
                epochs=200,
                batch_size=32,
                validation_data=(X_val, y_val),
                callbacks=[early_stopping],
            )
            loss = model.evaluate(X_test, y_test, verbose=1)
            model_dict['n_neurons'].append(nn)
            model_dict['n_layers'].append(nl)
            model_dict['loss'].append(loss)

    print(model_dict)'''
    #{'n_neurons': [200, 200, 200, 400, 400, 400, 600, 600, 600], 
    # 'n_layers': [1, 3, 5, 1, 3, 5, 1, 3, 5], 
    # 'loss': [22.695476531982422, 12.57523250579834, 10.627008438110352, 20.21051025390625, 8.998141288757324, 9.949676513671875, 20.923866271972656, 9.739904403686523, 15.194825172424316]}
    
    #{'n_neurons': [300, 300, 300, 400, 400, 400, 500, 500, 500], 
    # 'n_layers': [2, 3, 4, 2, 3, 4, 2, 3, 4], 
    # 'loss': [15.05650520324707, 11.52996826171875, 14.186291694641113, 14.572675704956055, 8.93062686920166, 9.00683879852295, 16.359643936157227, 10.516468048095703, 10.284761428833008]}
    #model.save("data/model")

    model = create_model(n_neurons=300, n_layers=4)
    model.fit(X_train, y_train, epochs=200, batch_size=32, validation_data=(X_val, y_val), callbacks=[early_stopping])
    test_loss = model.evaluate(X_test, y_test)
    print(f'test loss with unseen data: {str(test_loss)}')
    model.save("data/model")
