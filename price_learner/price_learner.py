import tensorflow as tf
import pandas as pd
from sklearn.model_selection import train_test_split

df = (
    pd.read_pickle("data/output.pkl")
    .set_index("itemid")
    .drop(columns=["timestamp"])
)
df["corrupted"] = df["corrupted"].astype(float)
X = pd.concat(
    [df.drop(columns=["price", "basetype"]), pd.get_dummies(df["basetype"])], axis=1
).astype(float).to_numpy()
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
    patience=5,
    verbose=0,
    mode="auto",
    baseline=None,
    restore_best_weights=False,
)


model = tf.keras.models.Sequential()
model.add(tf.keras.layers.Dense(400, activation="relu", input_shape=(313,)))
model.add(tf.keras.layers.Dense(400, activation="relu"))
model.add(tf.keras.layers.Dense(400, activation="relu"))
model.add(tf.keras.layers.Dense(1, activation="relu"))
model.compile(optimizer="adam", loss="mae")
model.fit(X_train, y_train, epochs=200, batch_size=32       , validation_data=(X_val, y_val), callbacks=[early_stopping])
model.evaluate(X_test, y_test, verbose=2)
