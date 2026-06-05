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

def run_replay(

    df,

    all_states,

    all_confidences,

    hour_arr,

    confidence_threshold,

    velocity_decay_threshold,

    base_hold,

    dynamic_hold_limit,

    loss_cut
):

    print()
    print("=== AFR REPLAY ENGINE V4 ===")
    print()


    # =====================================
    # LOAD DATA
    # =====================================
    raw_df = pd.read_csv(

        "data/raw/XAUUSD_M1.csv",

        sep="\t"
    )

    df = calculate_market_physics(
        raw_df
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

    MIN_PRESSURE = 0.03

    MIN_CONFIDENCE = 0.55

    MAX_EXHAUSTION = 0.80

    MIN_PROFIT_TO_EXIT = 0.50

    TRAILING_TRIGGER = 5.0 
    
    TRAILING_STOP = 1.0

    MIN_TREND_STRENGTH = 2.0

    MIN_RANGE_EXPANSION = 0.80

    MIN_ATR = 1.5

    COOLDOWN_CANDLES = 3

    SPREAD_COST = 0.10

    VERBOSE = False

    # =====================================
    # ACCOUNT
    # =====================================

    balance = 0

    gross_profit = 0

    gross_loss = 0

    wins = 0

    losses = 0

    recent_losses = 0

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

    exit_stats = {}

    # =====================================
    # NUMPY CACHE
    # =====================================

    close_arr = (
        df["close"].values
    )

    velocity_arr = (
        df["velocity"].values
    )

    pressure_arr = (
        df["pressure_delta"].values
    )

    range_arr = (
        df["range_expansion"].values
    )

    exhaustion_arr = (
        df["exhaustion_score"].values
    )

    chaos_arr = (
        df["chaos_regime"].values
    )

    atr_arr = (
        df["atr"].values
    )


    # =====================================
    # HTF TREND
    # =====================================

    m5_fast = (

        df["close"]

        .rolling(25)

        .mean()

        .values
    )

    m5_slow = (

        df["close"]

        .rolling(100)

        .mean()

        .values
    )

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

        # =====================================
        # HTF BIAS
        # =====================================

        bullish_htf = (

            m5_fast[i]
            >
            m5_slow[i]
        )

        bearish_htf = (

            m5_fast[i]
            <
            m5_slow[i]
        )

        trend_strength = abs(

            m5_fast[i]

            -

            m5_slow[i]
        )

        confidence = float(
            all_confidences[i]
        )

        current_price = float(
            close_arr[i]
        )

        hour = hour_arr[i]

        velocity = abs(
            velocity_arr[i]
        )

        pressure = abs(
            pressure_arr[i]
        )

        range_expansion = abs(
            range_arr[i]
        )

        exhaustion = float(
            exhaustion_arr[i]
        )

        chaos = int(
            chaos_arr[i]
        )


        # =====================================
        # IMPULSE COUNTER
        # =====================================

        if (

            state == "BULL_IMPULSE"

            or

            state == "BEAR_IMPULSE"
        ):

            rf_impulse_count += 1

        # =====================================
        # NO POSITION
        # =====================================

        if position is None:


            # =====================================
            # VALIDATE IMPULSE
            # =====================================

            validator_ok = False

            if (

                state == "BULL_IMPULSE"

                or

                state == "BEAR_IMPULSE"
            ):

                validator_ok = validate_impulse(

                    velocity,
                    pressure,
                    range_expansion,
                    confidence
                )


                prev_state = all_states[i - 1]

                same_direction = (

                    prev_state == state
                )

            # =====================================
            # VALIDATOR PASS
            # =====================================

            if (

                validator_ok

                and

                same_direction
            ):

                validator_pass_count += 1


                # =====================================
                # AI DIRECTION
                # =====================================

                direction = None

                if (

                    state == "BULL_IMPULSE"

                    and

                    bullish_htf

                    and

                    trend_strength
                    > MIN_TREND_STRENGTH
                ):

                    direction = "BUY"

                elif (

                    state == "BEAR_IMPULSE"

                    and

                    bearish_htf

                    and

                    trend_strength
                    > MIN_TREND_STRENGTH
                ):

                    direction = "SELL"

                if atr_arr[i] < MIN_ATR:

                    holds += 1

                    continue

                # =====================================
                # EXECUTE ENTRY
                # =====================================

                if chaos == 1:

                    continue

                # =====================================
                # REGIME FILTER
                # =====================================

                if (

                    range_expansion
                    < MIN_RANGE_EXPANSION
                ):

                    holds += 1

                    continue

                if direction is not None:

                    if direction == "BUY":

                        buy_count += 1

                    elif direction == "SELL":

                        sell_count += 1

                    if direction == "BUY":

                        entry_price = (

                            current_price
                            +
                            SPREAD_COST
                        )

                    else:

                        entry_price = (

                            current_price
                            -
                            SPREAD_COST
                        )
                    position = "OPEN"

                    entry_index = i

                    max_pnl = 0

                    entry_count += 1

                    if VERBOSE:

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
            # POSITION SIZE
            # =====================================

            position_size = (

                confidence
                *
                trend_strength
            ) / 10


            # =====================================
            # EQUITY CURVE PROTECTION
            # =====================================

            if recent_losses >= 3:

                position_size *= 0.50


            elif recent_losses >= 2:

                position_size *= 0.70

            # =====================================
            # PNL
            # =====================================

            if direction == "BUY":

                pnl = (

                    entry_price

                    -

                    current_price

                ) * position_size

            else:

                pnl = (

                    entry_price

                    -

                    current_price

                ) * position_size

            # =====================================
            # MAX PNL
            # =====================================

            if pnl > max_pnl:

                max_pnl = pnl

            # =====================================
            # VELOCITY HISTORY
            # =====================================

            velocity_now = abs(
                velocity_arr[i]
            )

            velocity_prev_1 = abs(
                velocity_arr[i - 1]
            )

            velocity_prev_2 = abs(
                velocity_arr[i - 2]
            )

            velocity_prev_3 = abs(
                velocity_arr[i - 3]
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

            dynamic_hold = base_hold


            if (

                velocity_decay > velocity_decay_threshold

                and

                pressure > 0.20
            ):

                dynamic_hold = dynamic_hold_limit


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
            # ADAPTIVE VELOCITY DECAY
            # =====================================

            elif (

                pnl < loss_cut

                and

                velocity_decay
                < velocity_decay_threshold

                and

                confidence < 0.70
            ):


                exit_trade = True

                exit_reason = (
                    "VELOCITY_DECAY"
                )

            # =====================================
            # ADAPTIVE PRESSURE COLLAPSE
            # =====================================

            elif (

                pnl < loss_cut

                and

                velocity_decay
                < velocity_decay_threshold

                and

                confidence < 0.70
            ):

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
            # ADAPTIVE EARLY LOSS CUT
            # =====================================

            elif (

                pnl < -1.5

                and

                pressure < 0.15
            ):

                exit_trade = True

                exit_reason = (
                    "EARLY_LOSS_CUT"
                )

            # =====================================
            # TRAILING EXIT
            # =====================================

            elif (

                max_pnl > TRAILING_TRIGGER

                and

                pnl < (

                    max_pnl
                    -
                    TRAILING_STOP
                )
            ):

                exit_trade = True

                exit_reason = (
                    "TRAILING_STOP"
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

                    recent_losses = 0

                    gross_profit += pnl

                else:

                    losses += 1

                    recent_losses += 1

                    gross_loss += abs(pnl)

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

                if exit_reason not in exit_stats:

                    exit_stats[
                        exit_reason
                    ] = 0

                exit_stats[
                    exit_reason
                ] += 1

                # =====================================
                # PRINT EXIT
                # =====================================

                if VERBOSE:

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


    # =====================================
    # FINAL REPORT
    # =====================================

    trades = wins + losses

    winrate = 0


    if trades > 0:

        winrate = (

            wins / trades
        ) * 100

        avg_win = (

            gross_profit

            /

            max(wins, 1)
        )

        avg_loss = (

            gross_loss

            /

            max(losses, 1)
        )

        profit_factor = (

            gross_profit

            /

            max(gross_loss, 0.0001)
        )

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

        print(
            f"AVG WIN    : {avg_win:.2f}"
        )

        print(
            f"AVG LOSS   : {avg_loss:.2f}"
        )

        print(
            f"PF         : {profit_factor:.2f}"
        )

        print()
        print("=== EXIT STATS ===")
        print()

        for reason, count in (

            exit_stats.items()
        ):

            print(
                f"{reason} : {count}"
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


        return {

            "balance": balance,

            "winrate": winrate,

            "trades": trades,

            "wins": wins,

            "losses": losses
        }

if __name__ == "__main__":

    print()
    print("[INFO] preload dataset...")
    print()


    from sensor.market_physics import (
        calculate_market_physics
    )

    from model.batch_inference import (
        batch_predict_states
    )

    import pandas as pd


    # =====================================
    # LOAD RAW DATA
    # =====================================

    raw_df = pd.read_csv(

        "data/raw/XAUUSD_M1.csv",

        sep="\t"
    )

    hour_arr = pd.to_datetime(

        raw_df["<TIME>"],

        format="%H:%M:%S"
        
    ).dt.hour.values

    # =====================================
    # PHYSICS
    # =====================================

    df = calculate_market_physics(
        raw_df
    )

    # =====================================
    # INFERENCE
    # =====================================

    all_states, all_confidences = (

        batch_predict_states(df)
    )

    print()
    print("[OK] preload complete")


    # =====================================
    # RUN REPLAY
    # =====================================

    run_replay(

        df=df,

        all_states=all_states,

        all_confidences=
        all_confidences,

        hour_arr=hour_arr,

        confidence_threshold=0.80,

        velocity_decay_threshold=0.40,

        base_hold=5,

        dynamic_hold_limit=15,

        loss_cut=-0.8
    )

    print()
    print(
        "[OK] trades_v3.csv saved"
    )

