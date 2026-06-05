import pandas as pd

from sensor.market_physics import (
    calculate_market_physics
)

from state.state_labeler import (
    label_market_states
)


print()
print("=== AFR DATASET PIPELINE ===")
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
    "[INFO] calculating market physics..."
)

df = calculate_market_physics(df)


# =====================================
# LABEL STATES
# =====================================

print(
    "[INFO] labeling market states..."
)

df = label_market_states(df)


# =====================================
# REPORT
# =====================================

print()
print("=== STATE DISTRIBUTION ===")
print()

print(
    df["state"]

    .value_counts()
)


print()

print(
    df.head()
)


print()

print(
    f"[FINAL ROWS] {len(df)}"
)


# =====================================
# EXPORT DATASET
# =====================================

output_path = (
    "data/processed/afr_dataset.csv"
)

df.to_csv(

    output_path,

    index=False
)


print()

print(
    f"[OK] dataset exported:"
)

print(
    output_path
)
