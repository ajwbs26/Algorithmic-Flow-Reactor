import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import psycopg2
import sys
import os

from datetime import datetime
from psycopg2.extras import RealDictCursor
from streamlit_autorefresh import st_autorefresh

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from telegram.config import (
    DB_HOST,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_PORT
)

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(

    page_title="AFR Dashboard",

    page_icon="⚡",

    layout="wide"
)

# ==================================================
# AUTO REFRESH
# ==================================================

st_autorefresh(

    interval=30000,

    key="afr_refresh"
)

# ==================================================
# CSS
# ==================================================

st.markdown("""

<style>

@import url(
'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700&display=swap'
);

:root {

    --bg-color:#0b0f14;

    --card-bg:#151921;

    --green:#00ff88;

    --red:#ff3366;

    --cyan:#00e5ff;

    --text:#848d9a;
}

html,
body,
[data-testid="stAppViewContainer"] {

    background-color:#0b0f14;
}

.stApp {

    background-color:#0b0f14;

    color:white;

    font-family:'Inter',sans-serif;
}

.kpi-card {

    background:#151921;

    padding:15px;

    border-radius:8px;

    border:1px solid #222;

    min-height:90px;
}

.kpi-label {

    color:#848d9a;

    font-size:10px;

    text-transform:uppercase;

    font-weight:700;
}

.kpi-value {

    font-size:22px;

    font-weight:700;

    margin-top:8px;

    font-family:'JetBrains Mono';
}

.kpi-delta {

    font-size:11px;

    margin-top:5px;
}

.online {

    color:#00ff88;
}

.offline {

    color:#ff3366;
}

.ai-panel {

    background:#151921;

    padding:15px;

    border-radius:8px;

    border:1px solid #222;
}

.ai-row {

    display:flex;

    justify-content:space-between;

    margin-bottom:8px;

    font-size:12px;
}

</style>

""", unsafe_allow_html=True)

# ==================================================
# DATABASE
# ==================================================

def get_connection():

    return psycopg2.connect(

        host=DB_HOST,

        database=DB_NAME,

        user=DB_USER,

        password=DB_PASSWORD,

        port=DB_PORT
    )


def query_db(sql, params=None):

    try:

        with get_connection() as conn:

            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(
                    sql,
                    params
                )

                if cur.description:

                    return pd.DataFrame(
                        cur.fetchall()
                    )

                return pd.DataFrame()

    except Exception as e:

        st.error(
            f"Database Error : {e}"
        )

        return pd.DataFrame()


# ==================================================
# HELPERS
# ==================================================

def prediction_to_signal(pred):

    if pred == 1:

        return "BUY"

    elif pred == 2:

        return "SELL"

    return "HOLD"


def chaos_to_text(regime):

    if regime == 0:

        return "LOW"

    elif regime == 1:

        return "MEDIUM"

    return "HIGH"


def get_system_status():

    engine_online = False

    last_engine_time = "N/A"

    live = query_db("""

        SELECT MAX(timestamp)

        AS last_time

        FROM afr_live_data

    """)

    if (

        not live.empty

        and

        live.iloc[0]["last_time"]
        is not None
    ):

        last_time = (
            live.iloc[0]["last_time"]
        )

        diff = (
            datetime.now()
            -
            last_time.replace(
                tzinfo=None
            )
        ).total_seconds()

        engine_online = (
            diff < 180
        )

        last_engine_time = (
            last_time.strftime(
                "%H:%M:%S"
            )
        )

    health = {}

    modules = [

        "TELEGRAM",

        "MT5",

        "FASTAPI",

        "AI_ENGINE"
    ]

    for module in modules:

        df = query_db(f"""

            SELECT timestamp

            FROM afr_system_log

            WHERE module='{module}'

            ORDER BY timestamp DESC

            LIMIT 1

        """)

        if not df.empty:

            ts = (
                df.iloc[0][
                    "timestamp"
                ]
            )

            diff = (

                datetime.now()

                -

                ts.replace(
                    tzinfo=None
                )

            ).total_seconds()

            health[module] = (
                diff < 300
            )

        else:

            health[module] = False

    return (

        engine_online,

        last_engine_time,

        health
    )


# ==================================================
# LOAD DATA
# ==================================================

trades_df = query_db("""

SELECT *

FROM closed_trades

ORDER BY exit_time

""")

live_df = query_db("""

SELECT *

FROM afr_live_data

ORDER BY timestamp DESC

LIMIT 1

""")

account_df = query_db("""

SELECT *

FROM afr_account_status

ORDER BY timestamp DESC

LIMIT 1

""")

errors_df = query_db("""

SELECT

timestamp,
module,
message

FROM afr_system_log

WHERE level='ERROR'

ORDER BY timestamp DESC

LIMIT 20

""")
# ==================================================
# HEADER
# ==================================================

col_l, col_m, col_r = st.columns(
    [2, 5, 3]
)

with col_l:

    st.markdown(
        """
        <div style="
        font-family:JetBrains Mono;
        font-size:28px;
        font-weight:800;
        ">
        AFR
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="
        color:#00e5ff;
        font-size:10px;
        letter-spacing:2px;
        ">
        ALGORITHMIC FLOW REACTOR
        </div>
        """,
        unsafe_allow_html=True
    )

with col_m:

    st.markdown(
        """
        <div style="
        display:flex;
        gap:20px;
        margin-top:15px;
        color:#848d9a;
        ">
            <span style="color:white;">
                Dashboard
            </span>

            <span>Trades</span>

            <span>Performance</span>

            <span>Sessions</span>

            <span>AI Analysis</span>

            <span>Reports</span>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_r:

    engine_status, engine_time, mod_health = (
        get_system_status()
    )

    if engine_status:

        txt = "🟢 ENGINE RUNNING"

        css = "online"

    else:

        txt = "🔴 ENGINE OFFLINE"

        css = "offline"

    st.markdown(

        f"""

        <div style="text-align:right;">

        <div class="{css}">

        {txt}

        </div>

        <div style="
        color:#848d9a;
        font-size:10px;
        ">

        Last Data :
        {engine_time}

        </div>

        </div>

        """,

        unsafe_allow_html=True
    )

st.divider()

# ==================================================
# KPI CALCULATION
# ==================================================

if not trades_df.empty:

    total_trades = len(
        trades_df
    )

    winners = trades_df[
        trades_df["pnl"] > 0
    ]

    losers = trades_df[
        trades_df["pnl"] < 0
    ]

    total_profit = (
        winners["pnl"].sum()
    )

    total_loss = (
        losers["pnl"].sum()
    )

    net_profit = (
        trades_df["pnl"].sum()
    )

    win_rate = (

        len(winners)

        /

        total_trades

    ) * 100

    profit_factor = (

        total_profit

        /

        abs(total_loss)

        if total_loss != 0

        else 0

    )

    trades_df = trades_df.sort_values(
        "exit_time"
    )

    trades_df["equity_curve"] = (

        trades_df["pnl"]
        .cumsum()
    )

else:

    total_trades = 0

    total_profit = 0

    total_loss = 0

    net_profit = 0

    win_rate = 0

    profit_factor = 0

# ==================================================
# KPI ROW
# ==================================================

cards = st.columns(8)

metrics = [

    (
        "NET PROFIT",
        f"${net_profit:,.2f}",
        "ALL TIME"
    ),

    (
        "AVG DAILY",
        f"${net_profit/30:,.2f}",
        "30 DAYS"
    ),

    (
        "TOTAL PROFIT",
        f"${total_profit:,.2f}",
        "WINNERS"
    ),

    (
        "TOTAL LOSS",
        f"${abs(total_loss):,.2f}",
        "LOSERS"
    ),

    (
        "WIN RATE",
        f"{win_rate:.1f}%",
        f"{total_trades} TRADES"
    ),

    (
        "TRADES",
        str(total_trades),
        "TOTAL"
    ),

    (
        "PROFIT FACTOR",
        f"{profit_factor:.2f}",
        "QUALITY"
    ),

    (
        "ENGINE",
        (
            "ONLINE"
            if engine_status
            else "OFFLINE"
        ),
        "STATUS"
    )
]

for i, metric in enumerate(metrics):

    label, value, delta = metric

    with cards[i]:

        st.markdown(

            f"""

            <div class="kpi-card">

            <div class="kpi-label">

            {label}

            </div>

            <div class="kpi-value">

            {value}

            </div>

            <div class="kpi-delta">

            {delta}

            </div>

            </div>

            """,

            unsafe_allow_html=True
        )

# ==================================================
# CHART ROW
# ==================================================

c1, c2, c3 = st.columns(
    [7, 2, 2]
)

# ==================================================
# EQUITY CURVE
# ==================================================

with c1:

    st.markdown(
        "##### Equity Curve"
    )

    if not trades_df.empty:

        fig = px.line(

            trades_df,

            x="exit_time",

            y="equity_curve",

            template="plotly_dark"
        )

        fig.update_layout(

            height=380,

            paper_bgcolor=
            "rgba(0,0,0,0)",

            plot_bgcolor=
            "rgba(0,0,0,0)"
        )

        st.plotly_chart(

            fig,

            use_container_width=True
        )

# ==================================================
# SESSION ANALYSIS
# ==================================================

with c2:

    st.markdown(
        "##### Session PnL"
    )

    if (

        not trades_df.empty

        and

        "session_name"
        in trades_df.columns
    ):

        session_df = (

            trades_df

            .groupby(
                "session_name"
            )["pnl"]

            .sum()

            .reset_index()
        )

        radar = go.Figure()

        radar.add_trace(

            go.Scatterpolar(

                r=session_df["pnl"],

                theta=session_df[
                    "session_name"
                ],

                fill="toself"
            )
        )

        radar.update_layout(

            template="plotly_dark",

            height=380
        )

        st.plotly_chart(

            radar,

            use_container_width=True
        )

# ==================================================
# SYSTEM HEALTH
# ==================================================

with c3:

    st.markdown(
        "##### System Health"
    )

    st.markdown(

        f"""
        MT5 :
        {'🟢' if mod_health.get('MT5') else '🔴'}
        """

    )

    st.markdown(

        f"""
        FastAPI :
        {'🟢' if mod_health.get('FASTAPI') else '🔴'}
        """

    )

    st.markdown(

        f"""
        Telegram :
        {'🟢' if mod_health.get('TELEGRAM') else '🔴'}
        """

    )

    st.markdown(

        f"""
        AI :
        {'🟢' if mod_health.get('AI_ENGINE') else '🔴'}
        """

    )

st.divider()

# ==================================================
# AI LIVE STATUS + WIN LOSS
# ==================================================

a1, a2 = st.columns(
    [6, 4]
)

with a1:

    st.markdown(
        "##### AI Live Status"
    )

    if not live_df.empty:

        ld = live_df.iloc[0]

        signal = prediction_to_signal(
            ld["prediction"]
        )

        regime = chaos_to_text(
            ld["chaos_regime"]
        )

        st.markdown(

            f"""

            <div class="ai-panel">

            <div class="ai-row">

            <span>Signal</span>

            <b>{signal}</b>

            </div>

            <div class="ai-row">

            <span>Confidence</span>

            <b>
            {ld["confidence"]*100:.2f}%
            </b>

            </div>

            <div class="ai-row">

            <span>Session</span>

            <b>
            {ld["session_name"]}
            </b>

            </div>

            <hr>

            <div class="ai-row">

            <span>Velocity</span>

            <b>
            {ld["velocity"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Momentum</span>

            <b>
            {ld["momentum_acceleration"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Buy Pressure</span>

            <b>
            {ld["buy_pressure"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Sell Pressure</span>

            <b>
            {ld["sell_pressure"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Pressure Delta</span>

            <b>
            {ld["pressure_delta"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Volatility</span>

            <b>
            {ld["volatility_shift"]:.4f}
            </b>

            </div>

            <div class="ai-row">

            <span>Regime</span>

            <b>
            {regime}
            </b>

            </div>

            <div class="ai-row">

            <span>Spread</span>

            <b>
            {ld["spread"]}
            </b>

            </div>

            </div>

            """,

            unsafe_allow_html=True
        )

with a2:

    st.markdown(
        "##### Win / Loss"
    )

    st.progress(
        float(
            win_rate / 100
        )
    )

    st.metric(

        "Win Rate",

        f"{win_rate:.2f}%"
    )

    st.metric(

        "Winning Trades",

        len(
            trades_df[
                trades_df["pnl"] > 0
            ]
        )
        if not trades_df.empty
        else 0
    )

    st.metric(

        "Losing Trades",

        len(
            trades_df[
                trades_df["pnl"] < 0
            ]
        )
        if not trades_df.empty
        else 0
    )

st.divider()

# ==================================================
# RECENT TRADES
# ==================================================

st.markdown(
    "### Recent Trades"
)

recent_trades = query_db("""

SELECT

entry_time,
exit_time,
symbol,
direction,
entry_price,
exit_price,
pnl,
confidence,
session_name,
hold_minutes,
exit_reason

FROM closed_trades

ORDER BY id DESC

LIMIT 20

""")

if not recent_trades.empty:

    st.dataframe(

        recent_trades,

        use_container_width=True,

        hide_index=True
    )

else:

    st.info(
        "No closed trades found."
    )

# ==================================================
# SYSTEM ERRORS
# ==================================================

st.markdown(
    "### System Errors"
)

if not errors_df.empty:

    st.dataframe(

        errors_df,

        use_container_width=True,

        hide_index=True
    )

else:

    st.success(
        "No system errors detected."
    )

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.title(
        "⚡ AFR"
    )

    st.caption(
        "Algorithmic Flow Reactor"
    )

    st.divider()

    st.subheader(
        "Account Status"
    )

    if not account_df.empty:

        acc = account_df.iloc[0]

        st.metric(

            "Balance",

            f"${acc['balance']:.2f}"
        )

        st.metric(

            "Equity",

            f"${acc['equity']:.2f}"
        )

        st.metric(

            "Profit",

            f"${acc['profit']:.2f}"
        )

        st.metric(

            "Open Positions",

            int(
                acc[
                    "open_positions"
                ]
            )
        )

        st.metric(

            "Leverage",

            f"1:{acc['leverage']}"
        )

    st.divider()

    st.subheader(
        "Engine Status"
    )

    if engine_status:

        st.success(
            "ENGINE ONLINE"
        )

    else:

        st.error(
            "ENGINE OFFLINE"
        )

    st.caption(
        f"Last Data : {engine_time}"
    )

    st.divider()

    st.subheader(
        "Latest Signal"
    )

    if not live_df.empty:

        st.info(

            prediction_to_signal(

                live_df.iloc[0][
                    "prediction"
                ]
            )
        )

        st.write(

            "Confidence:",

            f"{live_df.iloc[0]['confidence']*100:.2f}%"
        )

        st.write(

            "Session:",

            live_df.iloc[0][
                "session_name"
            ]
        )

    st.divider()

    st.subheader(
        "Database"
    )

    st.success(
        "PostgreSQL Connected"
    )

    st.divider()

    if st.button(
        "🔄 Refresh Dashboard"
    ):

        st.rerun()

# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(

    f"AFR Dashboard | "
    f"Last Refresh : "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)