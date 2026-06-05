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

from model.inference import (
    predict_market_state
)


print()
print("=== AFR SIMPLE REPLAY V1 ===")
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
# SETTINGS
# =====================================

CONFIDENCE_THRESHOLD = 0.80

MAX_HOLD_CANDLES = 5


# =====================================
# ACCOUNT
# =====================================

balance = 0

wins = 0

losses = 0

holds = 0


# =====================================
# POSITION
# =====================================

position = None

entry_price = 0

entry_index = 0


# =====================================
# LOOP
# =====================================

for i in range(

    50,

    len(df)
):

    current_df = df.iloc[:i+1]

    result = predict_market_state(
        current_df
    )


    state = result["state"]

    confidence = result[
        "confidence"
    ]


    current_price = (

        current_df.iloc[-1]["close"]
    )


    # =====================================
    # NO POSITION
    # =====================================

    if position is None:


        # =========================
        # ENTRY IMPULSE
        # =========================

        if (

            state == "IMPULSE"

            and

            confidence

            >=

            CONFIDENCE_THRESHOLD
        ):

            position = "BUY"

            entry_price = (
                current_price
            )

            entry_index = i

            print()

            print(
                f"[ENTRY] BUY"
            )

            print(
                f"PRICE      : {entry_price}"
            )

            print(
                f"CONFIDENCE : {confidence:.4f}"
            )


        else:

            holds += 1


    # =====================================
    # POSITION OPEN
    # =====================================

    else:

        hold_duration = (

            i - entry_index
        )


        pnl = (

            current_price

            -

            entry_price
        )


        # =========================
        # EXIT CONDITION
        # =========================

        exit_trade = False


        # EXIT EXHAUST
        if state == "EXHAUST":

            exit_trade = True


        # MAX HOLD
        elif (

            hold_duration

            >=

            MAX_HOLD_CANDLES
        ):

            exit_trade = True


        # LOW CONFIDENCE
        elif confidence < 0.50:

            exit_trade = True


        # =========================
        # EXECUTE EXIT
        # =========================

        if exit_trade:

            balance += pnl


            if pnl > 0:

                wins += 1

            else:

                losses += 1


            print()

            print(
                f"[EXIT] BUY"
            )

            print(
                f"PRICE      : {current_price}"
            )

            print(
                f"PNL        : {pnl:.2f}"
            )

            print(
                f"STATE      : {state}"
            )

            print(
                f"HOLD       : {hold_duration}"
            )


            # RESET
            position = None

            entry_price = 0

            entry_index = 0


# =====================================
# FINAL REPORT
# =====================================

trades = wins + losses

winrate = 0

if trades > 0:

    winrate = (

        wins / trades
    ) * 100


print()
print("=== REPLAY RESULT ===")
print()

print(
    f"WINS      : {wins}"
)

print(
    f"LOSSES    : {losses}"
)

print(
    f"HOLDS     : {holds}"
)

print(
    f"WINRATE   : {winrate:.2f}%"
)

print(
    f"BALANCE   : {balance:.2f}"
)

print(
    f"TRADES    : {trades}"
)
