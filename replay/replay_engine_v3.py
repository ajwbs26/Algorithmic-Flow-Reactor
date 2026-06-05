import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

import pandas as pd
import numpy as np


from sensor.market_physics import (
    calculate_market_physics
)

from model.batch_inference import (
    batch_predict_states
)

from execution.impulse_validator import (
    validate_impulse
)


print()
print("=== AFR REPLAY ENGINE V3 ===")
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

print(
    "[INFO] calculating physics..."
)

df = calculate_market_physics(df)

print(
    "[OK] physics complete"
)


# =====================================
# BATCH INFERENCE
# =====================================

print(
    "[INFO] batch inference..."
)

all_states, all_confidences = (

    batch_predict_states(df)
)

print(
    "[OK] inference complete"
)


# =====================================
# SETTINGS
# =====================================

CONFIDENCE_THRESHOLD = 0.90

MIN_PRESSURE = 0.05

MIN_CONFIDENCE = 0.55

MAX_EXHAUSTION = 0.80

COOLDOWN_CANDLES = 3

BASE_HOLD = 5


# =====================================
# ACCOUNT
# =====================================

balance = 0

wins = 0

losses = 0

holds = 0


# =====================================
# AUDIT COUNTER
# =====================================

rf_impulse_count = 0

validator_pass_count = 0

entry_count = 0

buy_count = 0

sell_count = 0

# =====================================
# POSITION
# =====================================

position = None

direction = None

entry_price = 0

entry_index = 0

cooldown_until = 0


# =====================================
# TRADE LOG
# =====================================

trade_log = []


# =====================================
# LOOP
# =====================================

for i in range(

    50,

    len(df)
):


    # =====================================
    # COOLDOWN
    # =====================================

    if i < cooldown_until:

        continue


    # =====================================
    # CURRENT DATA
    # =====================================

    state = all_states[i]

    confidence = float(
        all_confidences[i]
    )

    current_price = float(
        df.iloc[i]["close"]
    )

    velocity = abs(
        df.iloc[i]["velocity"]
    )

    pressure = abs(
        df.iloc[i]["pressure_delta"]
    )

    range_expansion = abs(
        df.iloc[i]["range_expansion"]
    )

    exhaustion = float(
        df.iloc[i]["exhaustion_score"]
    )

    chaos = int(
        df.iloc[i]["chaos_regime"]
    )


    # =====================================
    # IMPULSE COUNTER
    # =====================================

    if state == "IMPULSE":

        rf_impulse_count += 1


    # =====================================
    # NO POSITION
    # =====================================

    if position is None:


        # =====================================
        # VALIDATE IMPULSE
        # =====================================

        validator_ok = False


        if state == "IMPULSE":

            validator_ok = validate_impulse(

                velocity,
                pressure,
                range_expansion,
                confidence
            )


        # =====================================
        # VALIDATOR PASS
        # =====================================

        if validator_ok:

            validator_pass_count += 1


            # =====================================
            # BUY / SELL DETECTION
            # =====================================

            raw_velocity = float(
                df.iloc[i]["velocity"]
            )

            raw_pressure = float(
                df.iloc[i]["pressure_delta"]
            )


            # =====================================
            # TREND CONTEXT
            # =====================================

            slow_ma = (

                df["close"]

                .rolling(50)

                .mean()
            )

            current_ma = float(
                slow_ma.iloc[i]
            )

            current_close = float(
                df.iloc[i]["close"]
            )


            # =====================================
            # DIRECTION SCORE
            # =====================================

            direction_score = 0


            # =====================================
            # VELOCITY DIRECTION
            # =====================================

            if raw_velocity > 0:

                direction_score += 1

            else:

                direction_score -= 1


            # =====================================
            # PRESSURE DIRECTION
            # =====================================

            if raw_pressure > 0:

                direction_score += 1

            else:

                direction_score -= 1


            # =====================================
            # MOMENTUM DIRECTION
            # =====================================

            momentum = float(
                df.iloc[i]["momentum_acceleration"]
            )

            if momentum > 0:

                direction_score += 1

            else:

                direction_score -= 1


            # =====================================
            # TREND CONTEXT
            # =====================================

            slow_ma = (

                df["close"]

                .rolling(50)

                .mean()
            )

            current_ma = float(
                slow_ma.iloc[i]
            )

            current_close = float(
                df.iloc[i]["close"]
            )


            # =====================================
            # TREND BIAS
            # =====================================

            trend_bias = 0


            if current_close > current_ma:

                trend_bias += 1

            else:

                trend_bias -= 1


            direction_score += trend_bias


            # =====================================
            # FINAL DIRECTION
            # =====================================

            if direction_score > 0:

                direction = "BUY"


            elif direction_score < 0:

                direction = "SELL"


            else:

                if raw_velocity > 0:

                    direction = "BUY"

                else:

                    direction = "SELL"

            # =====================================
            # EXECUTE ENTRY
            # =====================================

            if direction is not None:

                # =====================================
                # BUY COUNT
                # =====================================

                if direction == "BUY":

                    buy_count += 1


                # =====================================
                # SELL COUNT
                # =====================================

                elif direction == "SELL":

                    sell_count += 1


                # =====================================
                # OPEN POSITION
                # =====================================

                position = "OPEN"

                entry_price = current_price

                entry_index = i

                entry_count += 1

                print()

                print(
                    f"[ENTRY] {direction}"
                )

                print(
                    f"PRICE      : {entry_price}"
                )

                print(
                    f"CONFIDENCE : {confidence:.4f}"
                )

                print(
                    f"VELOCITY   : {velocity:.4f}"
                )

                print(
                    f"PRESSURE   : {pressure:.4f}"
                )


        else:

            holds += 1

    # =====================================
    # POSITION OPEN
    # =====================================

    else:


        # =====================================
        # HOLD DURATION
        # =====================================

        hold_duration = (

            i - entry_index
        )


        # =====================================
        # PNL
        # =====================================

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
        # VELOCITY HISTORY
        # =====================================

        velocity_now = abs(
            df.iloc[i]["velocity"]
        )

        velocity_prev_1 = abs(
            df.iloc[i - 1]["velocity"]
        )

        velocity_prev_2 = abs(
            df.iloc[i - 2]["velocity"]
        )

        velocity_prev_3 = abs(
            df.iloc[i - 3]["velocity"]
        )


        # =====================================
        # VELOCITY AVERAGE
        # =====================================

        velocity_avg = (

            velocity_prev_1

            +

            velocity_prev_2

            +

            velocity_prev_3

        ) / 3


        # =====================================
        # VELOCITY DECAY
        # =====================================

        velocity_decay = (

            velocity_now

            /

            max(
                velocity_avg,
                0.0001
            )
        )


        # =====================================
        # DYNAMIC HOLD
        # =====================================

        dynamic_hold = BASE_HOLD


        if (

            velocity_decay > 0.80

            and

            pressure > 0.20
        ):

            dynamic_hold = 10


        # =====================================
        # EXIT LOGIC
        # =====================================

        exit_trade = False

        exit_reason = "UNKNOWN"


        # =====================================
        # EXHAUST EXIT
        # =====================================

        if state == "EXHAUST":

            exit_trade = True

            exit_reason = (
                "EXHAUST"
            )


        # =====================================
        # VELOCITY DECAY EXIT
        # =====================================

        elif velocity_decay < 0.50:

            exit_trade = True

            exit_reason = (
                "VELOCITY_DECAY"
            )


        # =====================================
        # PRESSURE COLLAPSE
        # =====================================

        elif pressure < MIN_PRESSURE:

            exit_trade = True

            exit_reason = (
                "PRESSURE_COLLAPSE"
            )


        # =====================================
        # EXHAUSTION SPIKE
        # =====================================

        elif exhaustion > MAX_EXHAUSTION:

            exit_trade = True

            exit_reason = (
                "EXHAUSTION_SPIKE"
            )


        # =====================================
        # CONFIDENCE COLLAPSE
        # =====================================

        elif confidence < MIN_CONFIDENCE:

            exit_trade = True

            exit_reason = (
                "CONFIDENCE_COLLAPSE"
            )


        # =====================================
        # MAX HOLD EXIT
        # =====================================

        elif hold_duration >= dynamic_hold:

            exit_trade = True

            exit_reason = (
                "MAX_HOLD"
            )


        # =====================================
        # EXECUTE EXIT
        # =====================================

        if exit_trade:


            # =====================================
            # ACCOUNT
            # =====================================

            balance += pnl


            if pnl > 0:

                wins += 1

            else:

                losses += 1


            # =====================================
            # TRADE LOG
            # =====================================

            trade_log.append({

                "direction": direction,

                "entry_price": entry_price,

                "exit_price": current_price,

                "hold": hold_duration,

                "pnl": pnl,

                "confidence": confidence,

                "state": state,

                "velocity_decay": velocity_decay,

                "exit_reason": exit_reason
            })


            # =====================================
            # PRINT EXIT
            # =====================================

            print()

            print(
                f"[EXIT] {direction}"
            )

            print(
                f"PRICE      : {current_price}"
            )

            print(
                f"PNL        : {pnl:.2f}"
            )

            print(
                f"VELOCITY   : {velocity:.4f}"
            )

            print(
                f"PRESSURE   : {pressure:.4f}"
            )

            print(
                f"DECAY      : {velocity_decay:.4f}"
            )

            print(
                f"EXHAUSTION : {exhaustion:.4f}"
            )

            print(
                f"CONFIDENCE : {confidence:.4f}"
            )

            print(
                f"STATE      : {state}"
            )

            print(
                f"HOLD       : {hold_duration}"
            )

            print(
                f"REASON     : {exit_reason}"
            )


            # =====================================
            # RESET POSITION
            # =====================================

            position = None

            direction = None

            entry_price = 0

            entry_index = 0


            # =====================================
            # COOLDOWN
            # =====================================

            cooldown_until = (

                i + COOLDOWN_CANDLES
            )


# =====================================
# SAVE CSV
# =====================================

pd.DataFrame(

    trade_log

).to_csv(

    "data/replay/trades_v3.csv",

    index=False
)

print()
print(
    "[OK] trades_v3.csv saved"
)


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
print("=== ENTRY PIPELINE ===")
print()

print(
    f"RF IMPULSE      : {rf_impulse_count}"
)

print(
    f"VALIDATOR PASS  : {validator_pass_count}"
)

print(
    f"REAL ENTRY      : {entry_count}"
)


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

print()
print("=== DIRECTION STATS ===")
print()

print(
    f"BUY       : {buy_count}"
)

print(
    f"SELL      : {sell_count}"
)

print(
    f"HOLD      : {holds}"
)