import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split

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

df = (
    pd.read_csv("data/output.csv", index_col=0)
    .set_index("itemid")
    .drop(columns=["timestamp"])
)
df["corrupted"] = df["corrupted"].astype(float)
X = pd.concat(
    [df.drop(columns=["price", "basetype"]), pd.get_dummies(df["basetype"])], axis=1
).to_numpy()
y = df["price"].to_numpy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.8, random_state=42
)

model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Dense(500, activation="relu", input_shape=(312,)))
model.add(tf.keras.layers.Dense(500, activation="relu"))
model.add(tf.keras.layers.Dense(500, activation="relu"))
model.add(tf.keras.layers.Dense(1, activation="relu"))
model.compile(optimizer="adam", loss="mse")
model.fit(X_train, y_train, epochs=50, batch_size=256)
model.evaluate(X_test, y_test, verbose=2)
