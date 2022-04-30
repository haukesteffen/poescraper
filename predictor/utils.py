import tensorflow as tf
import pandas as pd


def strip_digits(input_string):
    return "".join([i for i in input_string if i.isalpha() or i == " " or i == "(" or i == ")"])

def strip_alpha(input_string):
    return "".join([i for i in input_string if i.isnumeric() or i == " " or i == "."])

def convert_rolls(input_string):
    if not str.split(input_string):
        return 1.0
    else:
        value_list = [float(roll) for roll in str.split(input_string)]
        return sum(value_list)/len(value_list)

def convert_input(item_paste):
    item_dict = {}
    lexicon = pd.read_pickle('assets/lexicon.pkl')
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
    lexicon = pd.read_pickle('assets/lexicon.pkl')
    input_df = pd.DataFrame(input_dict, index=[0])
    item_df = pd.concat([lexicon, input_df], join='outer')
    item_df.fillna(0.0, inplace=True)
    item_df.set_index('itemid')
    basetype = item_df["basetype"]
    item_df[basetype] = 1.0
    return item_df

def estimate_price(input_item_df):
    model = tf.keras.models.load_model('assets/model')
    input_item_df.set_index('itemid', inplace=True)
    X = input_item_df.drop(columns=["basetype"]).astype(float).to_numpy()
    return model.predict_on_batch(X)