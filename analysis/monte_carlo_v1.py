import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


print()
print("=== AFR MONTE CARLO ===")
print()


# =====================================
# LOAD TRADES
# =====================================

df = pd.read_csv(

    "data/replay/trades_v3.csv"
)


# =====================================
# GET PNL
# =====================================

pnl_arr = df["pnl"].values


# =====================================
# SETTINGS
# =====================================

SIMULATIONS = 1000


final_balances = []

max_drawdowns = []

losing_streaks = []


# =====================================
# MONTE CARLO
# =====================================

for sim in range(SIMULATIONS):

    shuffled = np.random.permutation(
        pnl_arr
    )

    equity = [0]

    balance = 0

    peak = 0

    max_dd = 0

    current_losses = 0

    worst_losses = 0


    for pnl in shuffled:

        balance += pnl

        equity.append(balance)


        # =========================
        # DRAWDOWN
        # =========================

        if balance > peak:

            peak = balance


        drawdown = peak - balance


        if drawdown > max_dd:

            max_dd = drawdown


        # =========================
        # LOSING STREAK
        # =========================

        if pnl < 0:

            current_losses += 1


            if current_losses > worst_losses:

                worst_losses = current_losses

        else:

            current_losses = 0


    final_balances.append(
        balance
    )

    max_drawdowns.append(
        max_dd
    )

    losing_streaks.append(
        worst_losses
    )


# =====================================
# RESULT
# =====================================

print()
print("=== MONTE CARLO RESULT ===")
print()

print(
    f"SIMULATIONS        : {SIMULATIONS}"
)

print(
    f"AVG FINAL BALANCE  : "
    f"{np.mean(final_balances):.2f}"
)

print(
    f"WORST FINAL BALANCE: "
    f"{np.min(final_balances):.2f}"
)

print(
    f"BEST FINAL BALANCE : "
    f"{np.max(final_balances):.2f}"
)

print(
    f"AVG MAX DRAWDOWN   : "
    f"{np.mean(max_drawdowns):.2f}"
)

print(
    f"WORST DRAWDOWN     : "
    f"{np.max(max_drawdowns):.2f}"
)

print(
    f"AVG LOSING STREAK  : "
    f"{np.mean(losing_streaks):.2f}"
)

print(
    f"WORST LOSING STREAK: "
    f"{np.max(losing_streaks)}"
)

plt.hist(

    max_drawdowns,

    bins=50
)

