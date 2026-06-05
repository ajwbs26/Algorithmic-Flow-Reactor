import pandas as pd

from sensor.market_physics import (
    calculate_market_physics
)

from model.inference import (
    predict_market_state
)


print()
print("=== AFR REALTIME STATE ===")
print()


# =====================================
# LOAD DATA
# =====================================

df = pd.read_csv(

    "data/raw/XAUUSD_M1.csv",

    sep="\t"
)


# =====================================
# MARKET PHYSICS
# =====================================

df = calculate_market_physics(df)


# =====================================
# PREDICT
# =====================================

result = predict_market_state(df)


# =====================================
# OUTPUT
# =====================================

print()

print(
    f"STATE      : {result['state']}"
)

print(
    f"CONFIDENCE : {result['confidence']:.4f}"
)

print()

print(
    result["probabilities"]
)
