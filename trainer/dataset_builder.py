import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

import pandas as pd

from sensor.market_physics import (
    calculate_market_physics
)

from state.state_labeler import (
    label_market_states
)


print()
print("=== AFR DATASET BUILDER ===")
print()


# =====================================
# LOAD RAW DATA
# =====================================

df = pd.read_csv(

    "data/raw/XAUUSD_M1.csv",

    sep="\t"
)

print(
    f"[RAW ROWS] {len(df)}"
)


# =====================================
# MARKET PHYSICS
# =====================================

print()
print(
    "[INFO] calculating physics..."
)

df = calculate_market_physics(df)

print(
    "[OK] physics complete"
)


# =====================================
# LABEL STATES
# =====================================

print()
print(
    "[INFO] labeling states..."
)

df = label_market_states(df)

print(
    "[OK] labeling complete"
)


# =====================================
# SAVE DATASET
# =====================================

output_path = (

    "data/processed/"
    "afr_dataset_v4.csv"
)

df.to_csv(

    output_path,

    index=False
)

print()
print(
    f"[OK] dataset saved:"
)

print(
    output_path
)

print()
print(
    f"[FINAL ROWS] {len(df)}"
)

print()
print(
    df["state"]

    .value_counts()

    .sort_index()
)