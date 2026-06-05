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

df = pd.read_csv(
    "data/raw/XAUUSD_M1.csv",
    sep="\t"
)

df = calculate_market_physics(df)

print(df.columns.tolist())

print()
print(df.tail(3))