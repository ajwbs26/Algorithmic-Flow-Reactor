import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)


from replay.replay_engine_v4 import (
    run_replay
)



print()
print("=== AFR OPTIMIZER V1 ===")
print()

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


df = pd.read_csv(

    "data/raw/XAUUSD_M1.csv",

    sep="\t"
)

df = calculate_market_physics(df)

all_states, all_confidences = (

    batch_predict_states(df)
)

print(
    "[OK] preload complete"
)

# =====================================
# BEST RESULT
# =====================================

best_balance = -999999

best_config = None

results = []


# =====================================
# PARAMETER SPACE
# =====================================

confidence_values = [

    0.70,
    0.75,
    0.80
]

velocity_decay_values = [

    0.40,
    0.45,
    0.50
]

base_hold_values = [

    5,
    8
]

dynamic_hold_values = [

    15,
    20
]

loss_cut_values = [

    -0.3,
    -0.5
]

# =====================================
# LOOP
# =====================================

for confidence in confidence_values:

    for velocity_decay in velocity_decay_values:

        for base_hold in base_hold_values:

            for dynamic_hold in dynamic_hold_values:

                for loss_cut in loss_cut_values:


                    # =====================================
                    # RUN REPLAY
                    # =====================================

                    result = run_replay(

                        df=df,

                        all_states=all_states,

                        all_confidences=
                        all_confidences,

                        confidence_threshold=
                        confidence,

                        velocity_decay_threshold=
                        velocity_decay,

                        base_hold=
                        base_hold,

                        dynamic_hold_limit=
                        dynamic_hold,

                        loss_cut=
                        loss_cut
                    )

                    # =====================================
                    # EXTRACT RESULT
                    # =====================================

                    balance = result[
                        "balance"
                    ]

                    winrate = result[
                        "winrate"
                    ]

                    trades = result[
                        "trades"
                    ]


                    # =====================================
                    # SAVE RESULT
                    # =====================================

                    results.append({

                        "confidence":
                        confidence,

                        "velocity_decay":
                        velocity_decay,

                        "base_hold":
                        base_hold,

                        "dynamic_hold":
                        dynamic_hold,

                        "loss_cut":
                        loss_cut,

                        "balance":
                        balance,

                        "winrate":
                        winrate,

                        "trades":
                        trades
                    })


                    # =====================================
                    # PRINT RESULT
                    # =====================================

                    print()
                    print(
                        "===================="
                    )

                    print(
                        f"CONFIDENCE : {confidence}"
                    )

                    print(
                        f"DECAY      : {velocity_decay}"
                    )

                    print(
                        f"BASE HOLD  : {base_hold}"
                    )

                    print(
                        f"DYN HOLD   : {dynamic_hold}"
                    )

                    print(
                        f"LOSS CUT   : {loss_cut}"
                    )

                    print(
                        f"BALANCE    : {balance:.2f}"
                    )

                    print(
                        f"WINRATE    : {winrate:.2f}"
                    )

                    print(
                        f"TRADES     : {trades}"
                    )


                    # =====================================
                    # BEST CONFIG
                    # =====================================

                    if balance > best_balance:

                        best_balance = balance

                        best_config = {

                            "confidence":
                            confidence,

                            "velocity_decay":
                            velocity_decay,

                            "base_hold":
                            base_hold,

                            "dynamic_hold":
                            dynamic_hold,

                            "loss_cut":
                            loss_cut,

                            "balance":
                            balance,

                            "winrate":
                            winrate,

                            "trades":
                            trades
                        }


# =====================================
# FINAL RESULT
# =====================================

print()
print("=== BEST CONFIG ===")
print()

print(best_config)


# =====================================
# EXPORT CSV
# =====================================

os.makedirs(

    "optimizer/results",

    exist_ok=True
)

pd.DataFrame(

    results

).to_csv(

    "optimizer/results/"
    "optimizer_results.csv",

    index=False
)

print()
print(
    "[OK] optimizer_results.csv saved"
)

