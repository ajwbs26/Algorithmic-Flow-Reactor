from fastapi import FastAPI
from pydantic import BaseModel

import pandas as pd
import numpy as np
import joblib

app = FastAPI()

# =====================================
# LOAD MODEL
# =====================================

model = joblib.load(
    "model/afr_model.pkl"
)

quality_model = joblib.load(
    "models/trade_quality_model.joblib"
)

grade_model = joblib.load(
    "models/entry_grade_model.joblib"
)

FEATURE_COLUMNS = joblib.load(
    "model/feature_columns.pkl"
)

# =====================================
# REQUEST SCHEMA
# =====================================

class MarketData(BaseModel):

    velocity: float
    momentum_acceleration: float
    buy_pressure: float
    sell_pressure: float
    pressure_delta: float
    range_expansion: float
    volatility_shift: float
    velocity_exhaustion: float
    exhaustion_score: float
    chaos_regime: int

# =====================================
# ROOT
# =====================================

@app.get("/")
def root():

    return {
        "status": "AFR ONLINE"
    }

# =====================================
# PREDICT
# =====================================

@app.post("/predict")
def predict(data: MarketData):

    X_live = pd.DataFrame([{

        "velocity":
            data.velocity,

        "momentum_acceleration":
            data.momentum_acceleration,

        "buy_pressure":
            data.buy_pressure,

        "sell_pressure":
            data.sell_pressure,

        "pressure_delta":
            data.pressure_delta,

        "range_expansion":
            data.range_expansion,

        "volatility_shift":
            data.volatility_shift,

        "velocity_exhaustion":
            data.velocity_exhaustion,

        "exhaustion_score":
            data.exhaustion_score,

        "chaos_regime":
            data.chaos_regime
    }])

    X_live = X_live[
        FEATURE_COLUMNS
    ]

    prediction = int(
        model.predict(X_live)[0]
    )

    probabilities = model.predict_proba(
        X_live
    )[0]

    confidence = float(
        np.max(probabilities)
    )

    return {

        "prediction":
            prediction,

        "confidence":
            confidence,

        "probabilities": {

            "hold":
                float(probabilities[0]),

            "buy":
                float(probabilities[1]),

            "sell":
                float(probabilities[2]),

            "exit":
                float(probabilities[3])
        }
    }
