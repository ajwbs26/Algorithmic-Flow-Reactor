import psycopg2
import pandas as pd

# =====================================
# DATABASE
# =====================================

DB_CONFIG = {

    "host": "100.93.173.69",

    "database": "postgres",

    "user": "postgres",

    "password": "00000",

    "port": "5432"

}

# =====================================
# LOAD DATA
# =====================================

def load_trade_summary():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    df = pd.read_sql(
        """
        SELECT *
        FROM trade_summary
        """,
        conn
    )

    conn.close()

    return df


def load_ai_models():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    df = pd.read_sql(
        """
        SELECT *
        FROM ai_models
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()

    return df


def load_ai_learning_log():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    df = pd.read_sql(
        """
        SELECT *
        FROM ai_learning_log
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()

    return df

# =====================================
# TRADE ANALYSIS
# =====================================

def analyze_trade_stats(df):

    total_trades = len(df)

    wins = len(
        df[
            df["trade_result"] == "WIN"
        ]
    )

    losses = len(
        df[
            df["trade_result"] == "LOSS"
        ]
    )

    breakeven = len(
        df[
            df["trade_result"] == "BREAKEVEN"
        ]
    )

    win_rate = 0

    if total_trades > 0:

        win_rate = round(

            wins
            /
            total_trades
            *
            100,

            2

        )

    avg_pnl = round(

        df["pnl"].mean(),

        2

    )

    best_trade = round(

        df["pnl"].max(),

        2

    )

    worst_trade = round(

        df["pnl"].min(),

        2

    )

    return {

        "total_trades": total_trades,

        "wins": wins,

        "losses": losses,

        "breakeven": breakeven,

        "win_rate": win_rate,

        "avg_pnl": avg_pnl,

        "best_trade": best_trade,

        "worst_trade": worst_trade

    }

# =====================================
# SESSION ANALYSIS
# =====================================

def analyze_sessions(df):

    session_stats = (

        df.groupby(
            "session_name"
        )["pnl"]

        .mean()

        .sort_values(
            ascending=False
        )

    )

    best_session = (
        session_stats.index[0]
    )

    worst_session = (
        session_stats.index[-1]
    )

    return {

        "best_session":
        best_session,

        "worst_session":
        worst_session

    }


# =====================================
# ENERGY ANALYSIS
# =====================================

def analyze_energy(df):

    if (
        "energy_lifecycle"
        not in df.columns
    ):

        return {

            "best_energy":
            "N/A",

            "worst_energy":
            "N/A"

        }

    energy_stats = (

        df.groupby(
            "energy_lifecycle"
        )["pnl"]

        .mean()

        .sort_values(
            ascending=False
        )

    )

    return {

        "best_energy":
        energy_stats.index[0],

        "worst_energy":
        energy_stats.index[-1]

    }

# =====================================
# MODEL ANALYSIS
# =====================================

def analyze_models(df):

    if len(df) == 0:

        return {

            "current_model": "N/A",

            "best_model": "N/A",

            "best_score": 0

        }

    current_model = df.iloc[0][
        "model_version"
    ]

    best_row = df.loc[
        df[
            "trade_quality_score"
        ].idxmax()
    ]

    return {

        "current_model":
        current_model,

        "best_model":
        best_row[
            "model_version"
        ],

        "best_score":
        round(
            float(
                best_row[
                    "trade_quality_score"
                ]
            ),
            4
        )

    }


# =====================================
# LEARNING ANALYSIS
# =====================================

def analyze_learning(df):

    if len(df) == 0:

        return {

            "promoted": 0,

            "rejected": 0

        }

    promoted = len(

        df[
            df["decision"]
            ==
            "PROMOTED"
        ]

    )

    rejected = len(

        df[
            df["decision"]
            ==
            "REJECTED"
        ]

    )

    return {

        "promoted":
        promoted,

        "rejected":
        rejected

    }


# =====================================
# TOP FEATURE
# =====================================

def get_top_feature(df):

    if len(df) == 0:

        return "N/A"

    latest = df.iloc[0]

    features = {

        "confidence":
        latest[
            "confidence_importance"
        ],

        "entry_velocity":
        latest[
            "entry_velocity_importance"
        ],

        "entry_pressure":
        latest[
            "entry_pressure_importance"
        ],

        "range_expansion":
        latest[
            "range_expansion_importance"
        ],

        "volatility_shift":
        latest[
            "volatility_shift_importance"
        ],

        "exhaustion":
        latest[
            "exhaustion_importance"
        ],

        "chaos_regime":
        latest[
            "chaos_regime_importance"
        ],

        "velocity_delta":
        latest[
            "velocity_delta_importance"
        ],

        "pressure_delta":
        latest[
            "pressure_delta_importance"
        ],

        "exhaustion_delta":
        latest[
            "exhaustion_delta_importance"
        ]

    }

    return max(

        features,

        key=features.get

    )


# =====================================
# REPORT
# =====================================

def generate_report(

    trade_stats,

    session_stats,

    energy_stats,

    model_stats,

    learning_stats,

    top_feature

):

    print()

    print(
        "=" * 50
    )

    print(
        "AFR ANALYST REPORT"
    )

    print(
        "=" * 50
    )

    print()

    print(
        f"Trades : "
        f"{trade_stats['total_trades']}"
    )

    print(
        f"Win Rate : "
        f"{trade_stats['win_rate']}%"
    )

    print(
        f"Average PnL : "
        f"{trade_stats['avg_pnl']}"
    )

    print()

    print(
        f"Best Trade : "
        f"{trade_stats['best_trade']}"
    )

    print(
        f"Worst Trade : "
        f"{trade_stats['worst_trade']}"
    )

    print()

    print(
        f"Best Session : "
        f"{session_stats['best_session']}"
    )

    print(
        f"Worst Session : "
        f"{session_stats['worst_session']}"
    )

    print()

    print(
        f"Best Energy : "
        f"{energy_stats['best_energy']}"
    )

    print(
        f"Worst Energy : "
        f"{energy_stats['worst_energy']}"
    )

    print()

    print(
        f"Current Model : "
        f"{model_stats['current_model']}"
    )

    print(
        f"Best Model : "
        f"{model_stats['best_model']}"
    )

    print(
        f"Best Score : "
        f"{model_stats['best_score']}"
    )

    print()

    print(
        f"Promoted : "
        f"{learning_stats['promoted']}"
    )

    print(
        f"Rejected : "
        f"{learning_stats['rejected']}"
    )

    print()

    print(
        f"Top Feature : "
        f"{top_feature}"
    )

    print()

    print(
        "=" * 50
    )

# =====================================
# MAIN
# =====================================

def main():

    trade_df = (
        load_trade_summary()
    )

    models_df = (
        load_ai_models()
    )

    learning_df = (
        load_ai_learning_log()
    )

    trade_stats = (
        analyze_trade_stats(
            trade_df
        )
    )

    session_stats = (
        analyze_sessions(
            trade_df
        )
    )

    energy_stats = (
        analyze_energy(
            trade_df
        )
    )

    model_stats = (
        analyze_models(
            models_df
        )
    )

    learning_stats = (
        analyze_learning(
            learning_df
        )
    )

    top_feature = (
        get_top_feature(
            models_df
        )
    )

    generate_report(

        trade_stats,

        session_stats,

        energy_stats,

        model_stats,

        learning_stats,

        top_feature

    )


# =====================================
# RUN
# =====================================

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        print()

        print(
            "[ANALYST ERROR]"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )