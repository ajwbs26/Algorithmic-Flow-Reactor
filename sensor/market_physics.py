import numpy as np
import pandas as pd


# =====================================
# MARKET PHYSICS ENGINE
# =====================================

def calculate_market_physics(df):

    df = df.copy()


    # =====================================
    # CLEAN COLUMN
    # =====================================

    df.columns = [

        col.lower()

        .replace("<", "")

        .replace(">", "")

        .strip()

        for col in df.columns
    ]

    # =====================================
    # BASIC PRICE CHANGE
    # =====================================

    df["price_change"] = (

        df["close"].diff()
    )


    # =====================================
    # RAW RANGE
    # =====================================

    df["raw_range"] = (

        df["high"]

        -

        df["low"]
    )


    # =====================================
    # ATR
    # =====================================

    df["atr"] = (

        df["raw_range"]

        .rolling(14)

        .mean()
    )


    # =====================================
    # SAFETY
    # =====================================

    df["atr"] = (

        df["atr"]

        .replace(0, 0.00001)
    )


    # =====================================
    # VELOCITY
    # =====================================

    df["velocity"] = (

        df["price_change"]

        /

        df["atr"]
    )


    # =====================================
    # ACCELERATION
    # =====================================

    df["momentum_acceleration"] = (

        df["velocity"]

        .diff()
    )


    # =====================================
    # BODY
    # =====================================

    df["body"] = (

        df["close"]

        -

        df["open"]
    ).abs()


    # =====================================
    # TOTAL RANGE
    # =====================================

    df["total_range"] = (

        df["high"]

        -

        df["low"]
    )


    df["total_range"] = (

        df["total_range"]

        .replace(0, 0.00001)
    )


    # =====================================
    # BULLISH STRENGTH
    # =====================================

    df["bullish_strength"] = (

        (

            df["close"]

            -

            df["low"]
        )

        /

        df["total_range"]
    )


    # =====================================
    # BEARISH STRENGTH
    # =====================================

    df["bearish_strength"] = (

        (

            df["high"]

            -

            df["close"]
        )

        /

        df["total_range"]
    )


    # =====================================
    # BUY PRESSURE
    # =====================================

    df["buy_pressure"] = (

        df["body"]

        *

        df["bullish_strength"]
    )


    # =====================================
    # SELL PRESSURE
    # =====================================

    df["sell_pressure"] = (

        df["body"]

        *

        df["bearish_strength"]
    )


    # =====================================
    # PRESSURE DELTA
    # =====================================

    df["pressure_delta"] = (

        df["buy_pressure"]

        -

        df["sell_pressure"]
    )


    # =====================================
    # RANGE EXPANSION
    # =====================================

    df["range_expansion"] = (

        df["raw_range"]

        /

        df["atr"]
    )


    # =====================================
    # VOLATILITY SHIFT
    # =====================================

    short_vol = (

        df["raw_range"]

        .rolling(5)

        .mean()
    )

    long_vol = (

        df["raw_range"]

        .rolling(20)

        .mean()
    )


    df["volatility_shift"] = (

        short_vol

        -

        long_vol
    )


    # =====================================
    # VELOCITY EXHAUSTION
    # =====================================

    short_velocity = (

        df["velocity"]

        .rolling(3)

        .mean()
    )

    long_velocity = (

        df["velocity"]

        .rolling(8)

        .mean()
    )


    df["velocity_exhaustion"] = (

        short_velocity

        -

        long_velocity
    )


    # =====================================
    # UPPER WICK
    # =====================================

    df["upper_wick"] = (

        df["high"]

        -

        df[["open", "close"]]

        .max(axis=1)
    )


    # =====================================
    # LOWER WICK
    # =====================================

    df["lower_wick"] = (

        df[["open", "close"]]

        .min(axis=1)

        -

        df["low"]
    )


    # =====================================
    # WICK RATIO
    # =====================================

    df["upper_wick_ratio"] = (

        df["upper_wick"]

        /

        df["total_range"]
    )


    df["lower_wick_ratio"] = (

        df["lower_wick"]

        /

        df["total_range"]
    )


    # =====================================
    # EXHAUSTION SCORE
    # =====================================

    df["exhaustion_score"] = (

        (
            df["upper_wick_ratio"]

            +

            df["lower_wick_ratio"]
        )

        *

        abs(df["velocity_exhaustion"])
    )


    # =====================================
    # CHAOS REGIME
    # =====================================

    df["chaos_regime"] = np.where(

        (

            abs(df["pressure_delta"])

            <

            0.05
        )

        &

        (

            abs(df["velocity"])

            > 1.5
        ),

        1,

        0
    )


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
