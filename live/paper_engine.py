import psycopg2
import sys
import os
import joblib
import requests
import MetaTrader5 as mt5
import pandas as pd
import time
import csv

from datetime import datetime
from datetime import timedelta

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from sensor.market_physics import (
    calculate_market_physics
)

from database.trade_journal import (
    log_open_trade,
    update_closed_trade
)

from database.system_log import (
    log_error
)

# =====================================
# SETTINGS
# =====================================

def get_settings():

    import time

    for attempt in range(3):

        try:

            conn = psycopg2.connect(
                host="100.93.173.69",
                database="postgres",
                user="postgres",
                password="00000",
                port="5432",
                connect_timeout=10
            )

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    trading_enabled,
                    close_all
                FROM afr_settings
                WHERE id = 1
                """
            )

            row = cursor.fetchone()

            cursor.close()
            conn.close()

            return row

        except Exception as e:

            print(
                f"[SETTINGS RETRY {attempt+1}/3] {e}"
            )

            time.sleep(5)

    print(
        "[SETTINGS FAILED]"
    )

    return (
        True,
        False
    )

# =====================================
# CONSTANTS
# =====================================

SYMBOL = "XAUUSDm"

TIMEFRAME = mt5.TIMEFRAME_M1

LOT_SIZE = 0.01

MAGIC_NUMBER = 20260608

FASTAPI_URL = (
    "http://100.93.173.69:8000/predict"
)

LIVE_LOG_FILE = (
    "live/data/live_trades.csv"
)

CLOSED_TRADES_FILE = (
    "live/data/closed_trades.csv"
)

BREAKEVEN_TRIGGER = 2.0

TRAILING_TRIGGER = 5.0

TRAILING_DISTANCE = 2.0

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
# RUNTIME VARIABLES
# =====================================

last_candle_time = None

last_trade_candle = None

LAST_PROCESSED_DEAL = 0

ENTRY_TIME = None

ENTRY_PRICE = None

ENTRY_DIRECTION = None

ENTRY_CONFIDENCE = None

ENTRY_SESSION = None

ENTRY_VELOCITY = None

ENTRY_PRESSURE = None

# =====================================
# TELEGRAM
# =====================================

def telegram_send(text):

    try:

        requests.post(

            "https://api.telegram.org/bot8433625917:AAGg-VlK9chKb5kiU1dzVTiXTqFf1t0bqTw/sendMessage",

            json={

                "chat_id": "8708602484",

                "text": text

            },

            timeout=10
        )

    except Exception as e:

        print(
            f"[TELEGRAM ERROR] {e}"
        )

# =====================================
# MT5 CONNECT
# =====================================

print()
print("=== AFR LIVE PAPER ENGINE ===")
print()

if not mt5.initialize():

    print(
        "[ERROR] MT5 initialize failed"
    )

    quit()

print(
    "[OK] MT5 connected"
)

account_info = mt5.account_info()

print()
print("=== ACCOUNT INFO ===")

print(
    f"Balance      : {account_info.balance}"
)

print(
    f"Equity       : {account_info.equity}"
)

print(
    f"Profit       : {account_info.profit}"
)

print(
    f"Margin       : {account_info.margin}"
)

print(
    f"Free Margin  : {account_info.margin_free}"
)

print(
    f"Leverage     : {account_info.leverage}"
)

# =====================================
# LOAD MODEL
# =====================================

model = joblib.load(
    "model/afr_model.pkl"
)

print(
    "[OK] AI model loaded"
)

# =====================================
# CREATE LIVE LOG
# =====================================

if not os.path.exists(
    LIVE_LOG_FILE
):

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

            "current_price",

            "balance",

            "velocity",

            "buy_pressure",

            "sell_pressure",

            "range_expansion",

            "exhaustion_score"
        ])

# =====================================
# CREATE CLOSED LOG
# =====================================

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

            "exit_reason"
        ])

    # =====================================
    # CURRENT PRICE
    # =====================================

    current_price = float(
        latest["close"]
    )

    direction = "-"

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions:

        pos = positions[0]

        direction = (
            "BUY"
            if pos.type == mt5.POSITION_TYPE_BUY
            else "SELL"
        )

# =====================================
# DATABASE SAVE
# =====================================

def save_live_data(
    latest,
    prediction,
    confidence,
    spread,
    session_name
):

    conn = psycopg2.connect(
        host="100.93.173.69",
        database="postgres",
        user="postgres",
        password="00000",
        port="5432",

        connect_timeout=5
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO afr_live_data(

            timestamp,
            symbol,
            close_price,
            velocity,
            momentum_acceleration,
            buy_pressure,
            sell_pressure,
            pressure_delta,
            range_expansion,
            volatility_shift,
            velocity_exhaustion,
            exhaustion_score,
            chaos_regime,
            prediction,
            confidence,
            spread,
            session_name

        )

        VALUES(

            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s

        )
        """,
        (

            datetime.now(),

            SYMBOL,

            float(latest["close"]),

            float(latest["velocity"]),

            float(
                latest["momentum_acceleration"]
            ),

            float(
                latest["buy_pressure"]
            ),

            float(
                latest["sell_pressure"]
            ),

            float(
                latest["pressure_delta"]
            ),

            float(
                latest["range_expansion"]
            ),

            float(
                latest["volatility_shift"]
            ),

            float(
                latest["velocity_exhaustion"]
            ),

            float(
                latest["exhaustion_score"]
            ),

            int(
                latest["chaos_regime"]
            ),

            int(
                prediction
            ),

            float(
                confidence
            ),

            float(
                spread
            ),

            session_name
        )
    )

    account_info = mt5.account_info()

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    position_count = (
        len(positions)
        if positions
        else 0
    )

    cursor.execute(
        """
        INSERT INTO afr_account_status(

            timestamp,
            balance,
            equity,
            profit,
            margin,
            free_margin,
            leverage,
            open_positions

        )

        VALUES(

            %s,%s,%s,%s,%s,%s,%s,%s

        )
        """,
        (

            datetime.now(),

            float(
                account_info.balance
            ),

            float(
                account_info.equity
            ),

            float(
                account_info.profit
            ),

            float(
                account_info.margin
            ),

            float(
                account_info.margin_free
            ),

            int(
                account_info.leverage
            ),

            int(
                position_count
            )
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

# =====================================
# MAIN LOOP
# =====================================
LAST_SETTINGS_CHECK = 0

trading_enabled = True

close_all = False

while True:
    if (

        time.time()

        -

        LAST_SETTINGS_CHECK

        >

        60

    ):

        try:

            trading_enabled, close_all = (
                get_settings()
            )

            LAST_SETTINGS_CHECK = (
                time.time()
            )

        except Exception as e:

            print(
                f"[SETTINGS ERROR] {e}"
            )

    rates = mt5.copy_rates_from_pos(

        SYMBOL,

        TIMEFRAME,

        0,

        500
    )

    if rates is None:

        time.sleep(1)

        continue

    df = pd.DataFrame(
        rates
    )

    df["time"] = pd.to_datetime(

        df["time"],

        unit="s"
    )

    current_candle_time = (
        df.iloc[-1]["time"]
    )

    if (
        current_candle_time
        ==
        last_candle_time
    ):

        time.sleep(1)

        continue

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
    # MARKET PHYSICS
    # =====================================

    df = calculate_market_physics(
        df
    )

    print(
        "[OK] physics calculated"
    )

    latest = df.iloc[-1]

    velocity = latest["velocity"]

    momentum_acceleration = (
        latest["momentum_acceleration"]
    )

    pressure_delta = (
        latest["pressure_delta"]
    )

    exhaustion_score = (
        latest["exhaustion_score"]
    )

    # =====================================
    # ENERGY LIFECYCLE
    # =====================================

    if (

        velocity > 0

        and

        pressure_delta > 0

        and

        exhaustion_score < 0.25

    ):

        energy_lifecycle = "EXPANDING"

    elif (

        velocity < 0

        and

        pressure_delta < 0

    ):

        energy_lifecycle = "COLLAPSING"

    elif exhaustion_score > 0.25:

        energy_lifecycle = "EXHAUSTING"

    else:

        energy_lifecycle = "STABLE"

    payload = {

        "velocity":
            float(
                latest["velocity"]
            ),

        "momentum_acceleration":
            float(
                latest[
                    "momentum_acceleration"
                ]
            ),

        "buy_pressure":
            float(
                latest[
                    "buy_pressure"
                ]
            ),

        "sell_pressure":
            float(
                latest[
                    "sell_pressure"
                ]
            ),

        "pressure_delta":
            float(
                latest[
                    "pressure_delta"
                ]
            ),

        "range_expansion":
            float(
                latest[
                    "range_expansion"
                ]
            ),

        "volatility_shift":
            float(
                latest[
                    "volatility_shift"
                ]
            ),

        "velocity_exhaustion":
            float(
                latest[
                    "velocity_exhaustion"
                ]
            ),

        "exhaustion_score":
            float(
                latest[
                    "exhaustion_score"
                ]
            ),

        "chaos_regime":
            int(
                latest[
                    "chaos_regime"
                ]
            )
    }

    try:

        response = requests.post(

            FASTAPI_URL,

            json=payload,

            timeout=10
        )

        result = response.json()

    except Exception as e:

        log_error(
            "FASTAPI",
            str(e)
        )

        continue

    prediction = int(
        result["prediction"]
    )

    confidence = float(
        result["confidence"]
    )

    # =====================================
    # ENERGY PENALTY
    # =====================================

    if energy_lifecycle == "STABLE":

        confidence -= 0.15

    elif energy_lifecycle == "COLLAPSING":

        confidence += 0.05

    elif energy_lifecycle == "EXHAUSTING":

        confidence += 0.03

    elif energy_lifecycle == "EXPANDING":

        confidence += 0.01

    confidence = max(
        0.0,
        min(
            confidence,
            1.0
        )
    )

    print(
    f"[LIFECYCLE] {energy_lifecycle}"
    )

    print(
        f"[AI] prediction={prediction}"
    )

    print(
        f"[AI] confidence={confidence:.4f}"
    )

    # =====================================
    # SESSION CONFIDENCE MODIFIER
    # =====================================

    hour = current_candle_time.hour

    if 0 <= hour < 7:

        confidence -= 0.05

    elif 7 <= hour < 13:

        confidence -= 0.03

    else:

        confidence += 0.05

    confidence = max(
        0.0,
        min(
            confidence,
            1.0
        )
    )

    spread = float(
        latest["spread"]
    )

    print()
    print("[FEATURE DEBUG]")

    for col in FEATURE_COLUMNS:

        print(
            col,
            "=",
            latest[col]
        )

    print()

    print(
        latest[
            [
                "close",
                "velocity",
                "buy_pressure",
                "sell_pressure",
                "range_expansion",
                "exhaustion_score"
            ]
        ]
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
        f"[LIFECYCLE] "
        f"{energy_lifecycle}"
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

    hour = (
        current_candle_time.hour
    )

    if 0 <= hour < 7:

        session_name = "ASIA"

        min_confidence = 0.75

        max_spread = 350

        take_profit = 700

        stop_loss = 2

    elif 7 <= hour < 13:

        session_name = "LONDON"

        min_confidence = 0.75

        max_spread = 350

        stop_loss = 3

        take_profit = 700

    else:

        session_name = "NEW_YORK"

        min_confidence = 0.75

        max_spread = 350

        stop_loss = 3

        take_profit = 700
        
    print()

    print(
        f"[SESSION] "
        f"{session_name}"
    )

    print(
        f"[CHECK] "
        f"pred={prediction} "
        f"conf={confidence:.4f} "
        f"spread={spread}"
    )

    try:
        save_live_data(

            latest,

            prediction,

            confidence,

            spread,

            session_name
        )
    except Exception as e:
        print(
            f"[POSTGRES ERROR] {e}"
        )
        print(
            str(e)
        )
        print(
            "[ENGINE CONTINUE]"
        )
    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions is None:

        positions = []

    # =====================================
    # POSITION RECOVERY
    # =====================================

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions:

        print()

        print(
            "[POSITION RECOVERY]"
        )

        for pos in positions:

            print(
                f"Ticket : {pos.ticket}"
            )

            print(
                f"Type : {pos.type}"
            )

            print(
                f"Volume : {pos.volume}"
            )

            print(
                f"Open Price : "
                f"{pos.price_open}"
            )

            print(
                f"Current Profit : "
                f"{pos.profit}"
            )

    # =====================================
    # ENTRY FILTER
    # =====================================

    now = datetime.now()

    weekday = now.weekday()

    current_minutes = (
        now.hour * 60
        +
        now.minute
    )

    allow_entry = True

    # Sabtu setelah 03:29 WIB

    if (

        weekday == 5

        and

        current_minutes >= (3 * 60 + 29)

    ):

        allow_entry = False

        print(
            "[WEEKEND BLOCK]"
        )

    # Minggu penuh

    elif weekday == 6:

        allow_entry = False

        print(
            "[WEEKEND BLOCK]"
        )

    # Senin sebelum 04:05 WIB

    elif (

        weekday == 0

        and

        current_minutes < (4 * 60 + 5)

    ):

        allow_entry = False

        print(
            "[WEEKEND BLOCK]"
        )

    # =====================================
    # ENTRY ENGINE
    # =====================================

    if (

        allow_entry

        and

        len(positions) == 0

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

            price = mt5.symbol_info_tick(
                SYMBOL
            ).ask

            sl_price = price - stop_loss
            tp_price = price + take_profit

            request = {

                "action": mt5.TRADE_ACTION_DEAL,

                "symbol": SYMBOL,

                "volume": LOT_SIZE,

                "type": mt5.ORDER_TYPE_BUY,

                "price": price,

                "sl": sl_price,

                "tp": tp_price,

                "deviation": 20,

                "magic": 20260608,

                "comment": "AFR BUY",

                "type_time": mt5.ORDER_TIME_GTC,

                "type_filling": mt5.ORDER_FILLING_IOC
            }

            result = mt5.order_send(
                request
            )

            print(result)

            if result.retcode == mt5.TRADE_RETCODE_DONE:

                ENTRY_TIME = datetime.now()

                ENTRY_PRICE = result.price

                ENTRY_DIRECTION = "BUY"

                ENTRY_CONFIDENCE = confidence

                ENTRY_SESSION = session_name

                ENTRY_VELOCITY = velocity

                ENTRY_PRESSURE = pressure_delta

                position_ticket = result.order

                log_open_trade(

                    position_ticket=position_ticket,

                    entry_time=ENTRY_TIME,

                    symbol=SYMBOL,

                    direction=ENTRY_DIRECTION,

                    entry_price=ENTRY_PRICE,

                    confidence=ENTRY_CONFIDENCE,

                    entry_velocity=ENTRY_VELOCITY,

                    entry_pressure=ENTRY_PRESSURE,

                    session_name=ENTRY_SESSION,

                    trade_status="OPEN"

                )
                
                print(
                    "[BUY OPENED]"
                )
                
                print(
                    f"[SL] {sl_price}"
                )

                print(
                    f"[TP] {tp_price}"
                )

                last_trade_candle = (
                    current_candle_time
                )

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

            price = mt5.symbol_info_tick(
                SYMBOL
            ).bid

            sl_price = price + stop_loss
            tp_price = price - take_profit

            request = {

                "action": mt5.TRADE_ACTION_DEAL,

                "symbol": SYMBOL,

                "volume": LOT_SIZE,

                "type": mt5.ORDER_TYPE_SELL,

                "price": price,

                "sl": sl_price,

                "tp": tp_price,

                "deviation": 20,

                "magic": 20260608,

                "comment": "AFR SELL",

                "type_time": mt5.ORDER_TIME_GTC,

                "type_filling": mt5.ORDER_FILLING_IOC
            }

            result = mt5.order_send(
                request
            )

            print(result)

            if result.retcode == mt5.TRADE_RETCODE_DONE:

                ENTRY_TIME = datetime.now()

                ENTRY_PRICE = result.price

                ENTRY_DIRECTION = "SELL"

                ENTRY_CONFIDENCE = confidence

                ENTRY_SESSION = session_name

                ENTRY_VELOCITY = velocity

                ENTRY_PRESSURE = pressure_delta

                position_ticket = result.order

                log_open_trade(

                    position_ticket=position_ticket,

                    entry_time=ENTRY_TIME,

                    symbol=SYMBOL,

                    direction=ENTRY_DIRECTION,

                    entry_price=ENTRY_PRICE,

                    confidence=ENTRY_CONFIDENCE,

                    entry_velocity=ENTRY_VELOCITY,

                    entry_pressure=ENTRY_PRESSURE,

                    session_name=ENTRY_SESSION,

                    trade_status="OPEN"

                )
                
                print(
                    "[SELL OPENED]"
                )
                
                print(
                    f"[SL] {sl_price}"
                )

                print(
                    f"[TP] {tp_price}"
                )

                last_trade_candle = (
                    current_candle_time
                )

    # =====================================
    # POSITION MANAGEMENT
    # =====================================

    positions = mt5.positions_get(
        symbol=SYMBOL
    )

    if positions is None:

        positions = []

    for pos in positions:

        ticket = pos.ticket

        entry_price = (
            pos.price_open
        )

        current_sl = (
            pos.sl
        )

        current_tp = (
            pos.tp
        )

        profit = (
            pos.profit
        )

        entry_time = (
            datetime.fromtimestamp(
                pos.time
            )
        )

        direction = (

            "BUY"

            if pos.type
            ==
            mt5.POSITION_TYPE_BUY

            else

            "SELL"
        )

        tick = mt5.symbol_info_tick(
            SYMBOL
        )

        print()

        print(
            f"[POSITION] {ticket}"
        )

        print(
            f"[DIRECTION] {direction}"
        )

        print(
            f"[PROFIT] {profit:.2f}"
        )
        current_price = (

            tick.bid

            if pos.type ==
            mt5.POSITION_TYPE_BUY

            else

            tick.ask
        )

        distance = abs(
            current_price - entry_price
        )
        # =================================
        # BREAKEVEN
        # =================================

        if (

            distance >= 3.0

        ):

            if (

                pos.type
                ==
                mt5.POSITION_TYPE_BUY

            ):

                breakeven_sl = (
                    entry_price + 0.50
                )

                if (

                    current_sl
                    <
                    breakeven_sl

                ):

                    request = {

                        "action":
                            mt5.TRADE_ACTION_SLTP,

                        "symbol":
                            SYMBOL,

                        "position":
                            ticket,

                        "sl":
                            breakeven_sl,

                        "tp":
                            current_tp
                    }

                    result = mt5.order_send(
                        request
                    )

                    print(
                        "[BREAKEVEN BUY]"
                    )

                    print(
                        result
                    )

            else:

                breakeven_sl = (
                    entry_price - 0.50
                )

                if (

                    current_sl == 0

                    or

                    current_sl
                    >
                    breakeven_sl

                ):

                    request = {

                        "action":
                            mt5.TRADE_ACTION_SLTP,

                        "symbol":
                            SYMBOL,

                        "position":
                            ticket,

                        "sl":
                            breakeven_sl,

                        "tp":
                            current_tp
                    }

                    result = mt5.order_send(
                        request
                    )

                    print(
                        "[BREAKEVEN SELL]"
                    )

                    print(
                        result
                    )

        # =================================
        # ADAPTIVE TRAILING STOP
        # =================================

        if (

            distance >= 3.0

        ):

            if (

                pos.type
                ==
                mt5.POSITION_TYPE_BUY

            ):

                new_sl = (

                    tick.bid

                    -

                    TRAILING_DISTANCE

                )

                if (

                    new_sl
                    >
                    current_sl

                ):

                    request = {

                        "action":
                            mt5.TRADE_ACTION_SLTP,

                        "symbol":
                            SYMBOL,

                        "position":
                            ticket,

                        "sl":
                            new_sl,

                        "tp":
                            current_tp
                    }

                    result = mt5.order_send(
                        request
                    )

                    print(
                        f"[TRAIL BUY] "
                        f"{new_sl}"
                    )

                    print(
                        result
                    )

            else:

                new_sl = (

                    tick.ask

                    +

                    TRAILING_DISTANCE

                )

                if (

                    current_sl == 0

                    or

                    new_sl
                    <
                    current_sl

                ):

                    request = {

                        "action":
                            mt5.TRADE_ACTION_SLTP,

                        "symbol":
                            SYMBOL,

                        "position":
                            ticket,

                        "sl":
                            new_sl,

                        "tp":
                            current_tp
                    }

                    result = mt5.order_send(
                        request
                    )

                    print(
                        f"[TRAIL SELL] "
                        f"{new_sl}"
                    )

                    print(
                        result
                    )
        # =================================
        # SATS
        # =================================

        soft_exit = False

        if pos.profit > 0:

            if pos.type == mt5.POSITION_TYPE_BUY:

                if (

                    velocity < 0
                    and momentum_acceleration < 0
                    and pressure_delta < 0
                    and exhaustion_score > 0.25

                ):

                    soft_exit = True

            else:

                if (

                    velocity > 0
                    and momentum_acceleration > 0
                    and pressure_delta > 0
                    and exhaustion_score > 0.25

                ):

                    soft_exit = True

        if soft_exit:

            close_request = {

                "action":
                    mt5.TRADE_ACTION_DEAL,

                "symbol":
                    SYMBOL,

                "position":
                    ticket,

                "volume":
                    pos.volume,

                "type":

                    mt5.ORDER_TYPE_SELL

                    if

                    pos.type
                    ==
                    mt5.POSITION_TYPE_BUY

                    else

                    mt5.ORDER_TYPE_BUY,

                "price":

                    tick.bid

                    if

                    pos.type
                    ==
                    mt5.POSITION_TYPE_BUY

                    else

                    tick.ask,

                "deviation":
                    20,

                "magic":
                    MAGIC_NUMBER,

                "comment":
                    "AFR SATS EXIT"

            }

            result = mt5.order_send(
                close_request
            )

            print(
                "[SATS EXIT]"
            )

            print(
                result
            )
        # =================================
        # SAFETY CLOSE
        # =================================

        if (

            profit <= -15

        ):

            close_request = {

                "action":
                    mt5.TRADE_ACTION_DEAL,

                "symbol":
                    SYMBOL,

                "position":
                    ticket,

                "volume":
                    pos.volume,

                "type":

                    mt5.ORDER_TYPE_SELL

                    if

                    pos.type
                    ==
                    mt5.POSITION_TYPE_BUY

                    else

                    mt5.ORDER_TYPE_BUY,

                "price":

                    tick.bid

                    if

                    pos.type
                    ==
                    mt5.POSITION_TYPE_BUY

                    else

                    tick.ask,

                "deviation":
                    20,

                "magic":
                    MAGIC_NUMBER,

                "comment":
                    "AFR SAFETY CLOSE"
            }

            result = mt5.order_send(
                close_request
            )

            print(
                "[SAFETY CLOSE]"
            )

            print(
                result
            )

        allow_entry = True

        now = datetime.now()

        weekday = now.weekday()

        current_minutes = (
            now.hour * 60
            +
            now.minute
        )

        if weekday >= 5:

            allow_entry = False

            print(
                "[WEEKEND BLOCK]"
            )

        elif (

            weekday == 4

            and

            now.hour >= 20

        ):

            allow_entry = False

            print(
                "[FRIDAY BLOCK]"
            )

        elif (

            (20 * 60 + 30)

            <=

            current_minutes

            <=

            (22 * 60 + 10)

        ):

            allow_entry = False

            print(
                "[NO ENTRY ROLLOVER]"
            )

        if not trading_enabled:

            print(
                "[PAUSED BY TELEGRAM]"
            )

            time.sleep(1)

            continue

        if close_all:

            print(
                "[CLOSE ALL REQUEST]"
            )

            for pos in positions:

                tick = mt5.symbol_info_tick(
                    SYMBOL
                )

                request = {

                    "action":
                        mt5.TRADE_ACTION_DEAL,

                    "symbol":
                        SYMBOL,

                    "position":
                        pos.ticket,

                    "volume":
                        pos.volume,

                    "type":

                        mt5.ORDER_TYPE_SELL

                        if

                        pos.type
                        ==
                        mt5.POSITION_TYPE_BUY

                        else

                        mt5.ORDER_TYPE_BUY,

                    "price":

                        tick.bid

                        if

                        pos.type
                        ==
                        mt5.POSITION_TYPE_BUY

                        else

                        tick.ask,

                    "deviation":
                        20,

                    "magic":
                        MAGIC_NUMBER
                }

                mt5.order_send(
                    request
                )
        
            time.sleep(1)

            continue
    # =====================================
    # CLOSED TRADE SYNC
    # =====================================

    history = mt5.history_deals_get(

        datetime.now()
        -
        timedelta(hours=24),

        datetime.now()

    )

    if history:

        for deal in reversed(history):

            if deal.ticket == LAST_PROCESSED_DEAL:

                break

            if deal.entry != mt5.DEAL_ENTRY_OUT:

                continue
            
            print()

            print(
                "[CLOSED DEAL FOUND]"
            )

            print(
                deal._asdict()
            )

            print(
                f"[DEAL TICKET] {deal.ticket}"
            )

            print(
                f"[ORDER] {deal.order}"
            )

            print(
                f"[PROFIT] {deal.profit}"
            )

            print(
                f"[PRICE] {deal.price}"
            )

            update_closed_trade(

                position_ticket=deal.position_id,

                exit_time=datetime.fromtimestamp(
                    deal.time
                ),

                exit_price=float(
                    deal.price
                ),

                pnl=float(
                    deal.profit
                ),

                exit_reason=(

                    "PROFIT_CLOSE"

                    if deal.profit > 0

                    else

                    "LOSS_CLOSE"

                )

            )

            LAST_PROCESSED_DEAL = (
                deal.ticket
            )

            break
    # =====================================
    # HEARTBEAT
    # =====================================

    print()

    print(
        f"[ENGINE OK] "
        f"{datetime.now()}"
    )

    time.sleep(1)