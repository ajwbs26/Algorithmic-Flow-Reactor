import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


print()
print("=== AFR EQUITY CURVE ===")
print()


# =====================================
# LOAD TRADES
# =====================================

df = pd.read_csv(

    "data/replay/trades_v3.csv"
)


# =====================================
# PNL ARRAY
# =====================================

pnl_arr = df["pnl"].values


# =====================================
# EQUITY CURVE
# =====================================

equity_curve = np.cumsum(
    pnl_arr
)


# =====================================
# DRAWDOWN
# =====================================

peak_curve = np.maximum.accumulate(
    equity_curve
)

drawdown_curve = (
    peak_curve
    -
    equity_curve
)


# =====================================
# METRICS
# =====================================

max_drawdown = np.max(
    drawdown_curve
)

final_balance = equity_curve[-1]


print()
print("=== EQUITY RESULT ===")
print()

print(
    f"FINAL BALANCE : "
    f"{final_balance:.2f}"
)

print(
    f"MAX DRAWDOWN  : "
    f"{max_drawdown:.2f}"
)


# =====================================
# EQUITY CHART
# =====================================

plt.figure(figsize=(14, 6))

plt.plot(
    equity_curve
)

plt.title(
    "AFR Equity Curve"
)

plt.xlabel(
    "Trades"
)

plt.ylabel(
    "Balance"
)

plt.grid()

plt.show()


# =====================================
# DRAWDOWN CHART
# =====================================

plt.figure(figsize=(14, 4))

plt.plot(
    drawdown_curve
)

plt.title(
    "AFR Drawdown Curve"
)

plt.xlabel(
    "Trades"
)

plt.ylabel(
    "Drawdown"
)

plt.grid()

plt.show()