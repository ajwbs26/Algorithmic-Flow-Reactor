import joblib
import numpy as np
import pandas as pd


# =====================================
# LOAD MODEL
# =====================================

model = joblib.load(
    "model/afr_rf_model.pkl"
)

feature_columns = joblib.load(
    "model/feature_columns.pkl"
)


# =====================================
# STATE MAP
# =====================================

STATE_MAP = {

    0: "SLEEP",

    1: "IMPULSE",

    2: "EXHAUST"
}


# =====================================
# INFERENCE ENGINE
# =====================================

def predict_market_state(df):

    latest = df.iloc[-1:]


    # =====================================
    # FEATURE VECTOR
    # =====================================

    X = latest[
        feature_columns
    ]


    # =====================================
    # PREDICT
    # =====================================

    prediction = model.predict(
        X
    )[0]


    probabilities = (

        model.predict_proba(X)[0]
    )


    confidence = float(

        np.max(probabilities)
    )


    # =====================================
    # STATE
    # =====================================

    state = STATE_MAP[
        prediction
    ]


    return {

        "state":
            state,

        "confidence":
            confidence,

        "probabilities": {

            "sleep":
                probabilities[0],

            "impulse":
                probabilities[1],

            "exhaust":
                probabilities[2]
        }
    }
