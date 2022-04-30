#!/usr/bin/env python3

import os
import re
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from joblib import Parallel, delayed
from utils import convert_input, convert_dict_to_item_df, estimate_price


template = """
Item Class: Rings
Rarity: Rare
Damnation Eye
Sapphire Ring
--------
Requirements:
Level: 39
--------
Item Level: 71
--------
+29% to Cold Resistance (implicit)
--------
Adds 5 to 10 Physical Damage to Attacks
+42 to Accuracy Rating
+66 to maximum Life
+21 to maximum Mana
+5% to all Elemental Resistances
+31% to Lightning Resistance
"""

template2= '''
Item Class: Rings
Rarity: Rare
Chimeric Knuckle
Amethyst Ring
--------
Quality (Attribute Modifiers): +20% (augmented)
--------
Requirements:
Level: 65
--------
Item Level: 80
--------
Your Scout Towers have 25% increased Range (enchant)
--------
+22% to Chaos Resistance (implicit)
--------
+42 to Intelligence (fractured)
+10 to all Attributes
+67 to Dexterity
+42 to maximum Mana
+52 to maximum Life (crafted)
--------
Fractured Item
'''

template3 = '''
Item Class: Belts
Rarity: Rare
Nemesis Shackle
Synthesised Chain Belt
--------
Quality (Attribute Modifiers): +20% (augmented)
--------
Requirements:
Level: 65
--------
Item Level: 86
--------
18% increased Strength (implicit)
--------
+33 to Strength
+69 to Intelligence
+87 to maximum Life
+32% to Fire Resistance
8% chance for Flasks you use to not consume Charges (crafted)
--------
Synthesised Item
'''


def main():
    dict = convert_input(template2)
    df = convert_dict_to_item_df(dict)
    price = estimate_price(df)
    print(price[0][0])


if __name__ == "__main__":
    main()


###TODO
# load data in chunks to save memory
