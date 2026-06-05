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

    1: "BULL_IMPULSE",

    2: "BEAR_IMPULSE",

    3: "EXHAUST"
}

# =====================================
# BATCH INFERENCE
# =====================================

def batch_predict_states(df):

    X = df[
        feature_columns
    ]


    # =====================================
    # PREDICT ALL
    # =====================================

    predictions = model.predict(X)

    probabilities = (

        model.predict_proba(X)
    )


    # =====================================
    # STATE
    # =====================================

    states = [

        STATE_MAP[p]

        for p in predictions
    ]


    # =====================================
    # CONFIDENCE
    # =====================================

    confidences = np.max(

        probabilities,

        axis=1
    )


    return (

        np.array(states),

        np.array(confidences)
    )