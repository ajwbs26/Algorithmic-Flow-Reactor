import numpy as np
import pandas as pd


# =====================================
# STATE LABEL
# =====================================

SLEEP = 0

BULL_IMPULSE = 1

BEAR_IMPULSE = 2

EXHAUST = 3


# =====================================
# LABEL ENGINE
# =====================================

def label_market_states(

    df,

    future_window=5
):

    df = df.copy()

    labels = []


    # =====================================
    # LOOP
    # =====================================

    for i in range(

        len(df) - future_window
    ):

        current = df.iloc[i]

        future = df.iloc[

            i + 1 :

            i + future_window + 1
        ]


        # =====================================
        # CURRENT FEATURES
        # =====================================

        velocity = (

            current["velocity"]
        )

        acceleration = (

            current[
                "momentum_acceleration"
            ]
        )

        pressure = (

            current[
                "pressure_delta"
            ]
        )

        exhaustion = (

            current[
                "exhaustion_score"
            ]
        )

        chaos = (

            current[
                "chaos_regime"
            ]
        )


        # =====================================
        # FUTURE MOVEMENT
        # =====================================

        current_close = (
            current["close"]
        )

        future_close = (

            future["close"]

            .iloc[-1]
        )

        future_move = (

            future_close

            -

            current_close
        )


        # =====================================
        # NORMALIZED MOVE
        # =====================================

        atr = max(

            current["atr"],

            0.00001
        )

        normalized_move = (

            abs(future_move)

            /

            atr
        )


        # =====================================
        # BULL IMPULSE
        # =====================================

        bull_condition = (

            future_move > 0

            and

            normalized_move > 1.5

            and

            velocity > 0.5

            and

            pressure > 0.05

            and

            acceleration > 0
        )


        # =====================================
        # BEAR IMPULSE
        # =====================================

        bear_condition = (

            future_move < 0

            and

            normalized_move > 1.5

            and

            velocity < -0.5

            and

            pressure < -0.05

            and

            acceleration < 0
        )


        # =====================================
        # EXHAUST CONDITION
        # =====================================

        exhaust_condition = (

            exhaustion > 0.5

            and

            abs(velocity) < 0.3
        )


        # =====================================
        # CHAOS OVERRIDE
        # =====================================

        if chaos == 1:

            label = SLEEP


        # =====================================
        # BULL IMPULSE
        # =====================================

        elif bull_condition:

            label = BULL_IMPULSE


        # =====================================
        # BEAR IMPULSE
        # =====================================

        elif bear_condition:

            label = BEAR_IMPULSE


        # =====================================
        # EXHAUST
        # =====================================

        elif exhaust_condition:

            label = EXHAUST


        # =====================================
        # DEFAULT
        # =====================================

        else:

            label = SLEEP


        labels.append(label)


    # =====================================
    # FINALIZE
    # =====================================

    df = df.iloc[:len(labels)]

    df["state"] = labels


    # =====================================
    # CLEAN
    # =====================================

    df = df.replace(

        [np.inf, -np.inf],

        np.nan
    )

    df = df.dropna()

    df = df.reset_index(
        drop=True
    )


    return df