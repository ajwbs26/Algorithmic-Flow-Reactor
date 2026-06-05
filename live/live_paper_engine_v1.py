import sys
import os
import joblib
import numpy as np


sys.path.append(

    os.path.dirname(

        os.path.dirname(__file__)
    )
)


import MetaTrader5 as mt5
import pandas as pd
import time
import csv

from sensor.market_physics import (
    calculate_market_physics
)

print()
print("=== AFR LIVE PAPER ENGINE ===")
print()

# =====================================
# MT5 CONNECT
# =====================================

if not mt5.initialize():

    print(
        "[ERROR] MT5 initialize failed"
    )

    quit()


print(
    "[OK] MT5 connected"
)

# =====================================
# LOAD MODEL
# =====================================

model = joblib.load(

    "model/afr_rf_model.pkl"
)

print(
    "[OK] AI model loaded"
)

FEATURE_COLUMNS = [

    "velocity",

    "momentum_acceleration",

    "buy_pressure",

    "sell_pressure",

    "pressure_delta",

    "range_expansion",

    "volatility_shift",

    "velocity_exhaustion",

    "exhaustion_score",

    "chaos_regime"
]

# =====================================
# PAPER ACCOUNT
# =====================================

paper_balance = 1000

SYMBOL = "XAUUSDm"

TIMEFRAME = mt5.TIMEFRAME_M1

last_candle_time = None

position = None

entry_price = 0.0

entry_time = None

direction = None

last_trade_candle = None

CLOSED_TRADES_FILE = (
    "live/data/closed_trades.csv"
        
)
LIVE_LOG_FILE = (
    "live/data/live_trades.csv"
)

if not os.path.exists(
    LIVE_LOG_FILE
):

    print(
        "[DEBUG] writing csv..."
    )

    with open(

        LIVE_LOG_FILE,

        mode="w",

        newline=""

    ) as file:


        writer = csv.writer(
            file
        )


        writer.writerow([

            "time",

            "prediction",

            "confidence",

            "direction",

            "entry_price",

            "current_price",

            "pnl",

            "paper_balance",

            "velocity",

            "buy_pressure",

            "sell_pressure",

            "range_expansion",

            "exhaustion_score"
        ])

if not os.path.exists(
    CLOSED_TRADES_FILE
):

    with open(

        CLOSED_TRADES_FILE,

        mode="w",

        newline=""
    ) as file:


        writer = csv.writer(
            file
        )


        writer.writerow([

            "entry_time",

            "exit_time",

            "direction",

            "entry_price",

            "exit_price",

            "pnl",

            "balance",

            "reason"
        ])

# =====================================
# MAIN LOOP
# =====================================

while True:

    # =====================================
    # LOAD LIVE CANDLES
    # =====================================

    rates = mt5.copy_rates_from_pos(

        SYMBOL,

        TIMEFRAME,

        0,

        500
    )

    df = pd.DataFrame(
        rates
    )

    # =====================================
    # TIME CONVERT
    # =====================================

    df["time"] = pd.to_datetime(

        df["time"],

        unit="s"
    )

    current_candle_time = (

        df.iloc[-1]["time"]
    )

    # =====================================
    # SAME CANDLE
    # =====================================

    if (

        current_candle_time
        ==
        last_candle_time
    ):

        time.sleep(1)

        continue

    # =====================================
    # NEW CANDLE
    # =====================================

    last_candle_time = (
        current_candle_time
    )


    print()
    print("=" * 50)

    print(
        f"[NEW CANDLE] "
        f"{current_candle_time}"
    )


    # =====================================
    # CALCULATE PHYSICS
    # =====================================

    df = calculate_market_physics(
        df
    )


    print(
        "[OK] physics calculated"
    )


    # =====================================
    # LAST ROW
    # =====================================

    latest = df.iloc[-1]

    X_live = pd.DataFrame([
        latest[FEATURE_COLUMNS]
    ])

    prediction = model.predict(
        X_live
    )[0]

    confidence = np.max(
        model.predict_proba(
            X_live
        )
    )

    proba = model.predict_proba(
        X_live
    )[0]

    print()
    print("[PROBABILITY]")
    print(
        f"HOLD={proba[0]:.4f} "
        f"BUY={proba[1]:.4f} "
        f"SELL={proba[2]:.4f} "
        f"EXIT={proba[3]:.4f}"
    )
    print()
    print("[FEATURE DEBUG]")

    for col in FEATURE_COLUMNS:
        print(
            col,
            "=",
            latest[col]
        )

    spread = float(
        latest["spread"]
    )

    # =====================================
    # SHOW PHYSICS
    # =====================================

    print()

    print(

        latest[[
            "close",
            "velocity",
            "buy_pressure",
            "sell_pressure",
            "range_expansion",
            "exhaustion_score"
        ]]
    )


    # =====================================
    # FEATURES
    # =====================================

    X_live = pd.DataFrame([

        latest[FEATURE_COLUMNS]
    ])


    # =====================================
    # AI PREDICT
    # =====================================

    prediction = model.predict(
        X_live
    )[0]


    confidence = np.max(

        model.predict_proba(
            X_live
        )
    )


    print()

    print(
        f"[AI] prediction : "
        f"{prediction}"
    )

    print(
        f"[AI] confidence : "
        f"{confidence:.4f}"
    )

    print(
        f"[SPREAD] "
        f"{spread}"
    )

    # =====================================
    # SESSION DETECTOR
    # =====================================

    hour = current_candle_time.hour


    if 0 <= hour < 7:

        session = "ASIA"

        min_confidence = 0.50

        max_spread = 9999

        take_profit = 3

        stop_loss = 2


    elif 7 <= hour < 13:

        session = "LONDON"

        min_confidence = 0.75

        max_spread = 350

        take_profit = 5

        stop_loss = 3


    else:

        session = "NEW_YORK"

        min_confidence = 0.75

        max_spread = 350

        take_profit = 5

        stop_loss = 3


    print()

    print(
        f"[SESSION] "
        f"{session}"
    )
    print(
        f"[CHECK] pred={prediction} "
        f"conf={confidence:.4f} "
        f"spread={spread}"
    )
    proba = model.predict_proba(X_live)[0]
    # =====================================
    # ENTRY ENGINE
    # =====================================

    if (

        position is None

        and

        last_trade_candle
        !=
        current_candle_time
    ):



        # ================================
        # BUY
        # ================================

        if (

            prediction == 1

            and

            confidence > min_confidence

            and

            spread <= max_spread
        ):

            position = "OPEN"

            direction = "BUY"

            entry_price = float(
                latest["close"]
            )

            entry_time = (
                current_candle_time
            )

            last_trade_candle = (
                current_candle_time
            )

            print()

            print(
                f"[ENTRY BUY] "
                f"{entry_price}"
            )
            print("[BUY SIGNAL DETECTED]")

        # ================================
        # SELL
        # ================================

        elif (

            prediction == 2

            and

            confidence > min_confidence

            and

            spread <= max_spread

        ):

            position = "OPEN"

            direction = "SELL"

            entry_price = float(
                latest["close"]
            )

            entry_time = (
                current_candle_time
            )

            last_trade_candle = (
                current_candle_time
            )


            print()

            print(
                f"[ENTRY SELL] "
                f"{entry_price}"
            )
            print("[SELL SIGNAL DETECTED]")

    # =====================================
    # CURRENT PRICE
    # =====================================

    current_price = float(
        latest["close"]
    )


    # =====================================
    # LIVE PNL
    # =====================================

    pnl = 0.0


    if position == "OPEN":


        if direction == "BUY":

            pnl = (

                current_price
                -
                entry_price
            )

        else:

            pnl = (

                entry_price
                -
                current_price
            )


    # =====================================
    # SAVE LIVE DATA
    # =====================================

    with open(

        LIVE_LOG_FILE,

        mode="a",

        newline=""
    ) as file:


        writer = csv.writer(
            file
        )


        writer.writerow([

            current_candle_time,

            prediction,

            confidence,

            direction,

            entry_price,

            current_price,

            pnl,

            paper_balance,

            latest["velocity"],

            latest["buy_pressure"],

            latest["sell_pressure"],

            latest["range_expansion"],

            latest["exhaustion_score"]
        ])


    print()

    print(
        "[OK] live data saved"
    )


    # =====================================
    # EXIT ENGINE
    # =====================================

    if position == "OPEN":


        if pnl > take_profit:


            paper_balance += pnl


            print()

            print(
                f"[TP CLOSE] "
                f"{pnl:.2f}"
            )

            print(
                f"[BALANCE] "
                f"{paper_balance:.2f}"
            )

            with open(

                CLOSED_TRADES_FILE,

                mode="a",

                newline=""
            ) as file:


                writer = csv.writer(
                    file
                )


                writer.writerow([

                    entry_time,

                    current_candle_time,

                    direction,

                    entry_price,

                    current_price,

                    pnl,

                    paper_balance,

                    "TAKE_PROFIT"
                ])

            position = None

            direction = None

            last_trade_candle = None

        elif pnl < -stop_loss:

            paper_balance += pnl

            print()

            print(
                f"[SL CLOSE] "
                f"{pnl:.2f}"
            )

            print(
                f"[BALANCE] "
                f"{paper_balance:.2f}"
            )

            with open(

                CLOSED_TRADES_FILE,

                mode="a",

                newline=""
            ) as file:


                writer = csv.writer(
                    file
                )


                writer.writerow([

                    entry_time,

                    current_candle_time,

                    direction,

                    entry_price,

                    current_price,

                    pnl,

                    paper_balance,

                    "STOP_LOSS"
                ])
            position = None

            direction = None

            last_trade_candle = None


    time.sleep(1)
