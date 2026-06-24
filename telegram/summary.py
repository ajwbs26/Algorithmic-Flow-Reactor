import time
import psycopg2
import traceback

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

 # SNAPSHOT

 # =====================================

def get_snapshot(
    cursor,
    target_time
):

    cursor.execute(
        """
        SELECT *

        FROM afr_live_data

        ORDER BY ABS(
            EXTRACT(
                EPOCH FROM (
                    timestamp - %s
                )
            )
        )

        LIMIT 1
        """,
        (
            target_time,
        )
    )

    row = cursor.fetchone()

    if row is None:

        return None

    columns = [

        desc[0]
        for desc
        in cursor.description

    ]

    return dict(
        zip(
            columns,
            row
        )
    )

 # =====================================

 # TRADE QUALITY

 # =====================================

def calculate_trade_quality(

    confidence,

    velocity,

    pressure,

    pnl

):

    pnl_score = min(

        abs(
            pnl
        ) / 5,

        1.0
    )

    score = (

        confidence * 0.40 +

        min(
            abs(
                velocity
            ),
            1.0
        ) * 0.20 +

        min(
            abs(
                pressure
            ),
            1.0
        ) * 0.20 +

        pnl_score * 0.20

    )

    score = max(
        0,
        min(
            score,
            1
        )
    )

    return round(
        score,
        4
    )

 # =====================================
 # TRADE LIFECYCLE
 # =====================================

def get_trade_lifecycle(
    hold_minutes
):

    if hold_minutes <= 2:

        return "FLASH"

    elif hold_minutes <= 10:

        return "MOMENTUM"

    elif hold_minutes <= 30:

        return "TREND"

    else:

        return "EXTENDED"

 # =====================================

 # ENTRY GRADE

 # =====================================

def calculate_entry_grade(

    trade_quality

):

    if trade_quality >= 0.90:

        return "A+"

    elif trade_quality >= 0.80:

        return "A"

    elif trade_quality >= 0.70:

        return "B"

    elif trade_quality >= 0.60:

        return "C"

    else:

        return "D"

 # =====================================

 # MARKET SUPPORT

 # =====================================

def calculate_market_support(

    entry_velocity,

    exit_velocity,

    entry_pressure,

    exit_pressure

):

    support_score = 0

    if exit_velocity > entry_velocity:

        support_score += 1

    if exit_pressure > entry_pressure:

        support_score += 1

    if support_score == 2:

        return "SUPPORTED"

    elif support_score == 1:

        return "NEUTRAL"

    else:

        return "COLLAPSING"

 # =====================================

 # EXIT QUALITY

 # =====================================

def calculate_exit_quality(

    pnl,

    entry_velocity,

    exit_velocity,

    exit_exhaustion

):

    if (

        pnl > 0

        and

        exit_velocity > entry_velocity

    ):

        return "EARLY_EXIT"

    elif (

        pnl > 0

        and

        exit_velocity <= entry_velocity

    ):

        return "GOOD_EXIT"

    elif (

        pnl < 0

        and

        exit_exhaustion > 0.70

    ):

        return "LATE_EXIT"

    else:

        return "NORMAL_EXIT"

 # =====================================

 # ENERGY STATE

 # =====================================

def calculate_energy_state(

    velocity,

    pressure,

    exhaustion,

    chaos

):

    if chaos == 1:

        return "CHAOS"

    elif exhaustion > 0.70:

        return "DECAY"

    elif (

        velocity > 0.50

        and

        pressure > 0.50

    ):

        return "GROWTH"

    else:

        return "NEUTRAL"

 # =====================================

 # PROCESS TRADE SUMMARY

 # =====================================

def process_trade_summary():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    cursor = conn.cursor()

    cursor.execute(
        
        """
        SELECT *

        FROM closed_trades

        WHERE processed = false
        ORDER BY id ASC

        """
    )

    trades = cursor.fetchall()

    if not trades:

        print(
            "[SUMMARY] No new trade"
        )

        cursor.close()
        conn.close()

        return

    columns = [

        desc[0]
        for desc
        in cursor.description

    ]

    for trade in trades:

        row = dict(
            zip(
                columns,
                trade
            )
        )

        entry_snapshot = get_snapshot(

            cursor,

            row["entry_time"]

        )

        exit_snapshot = get_snapshot(

            cursor,

            row["exit_time"]

        )

        if (

            entry_snapshot is None

            or

            exit_snapshot is None

        ):

            print(
                "[WARNING] Snapshot not found"
            )

            continue


        velocity_delta = (

            exit_snapshot["velocity"]

            -

            entry_snapshot["velocity"]

        )

        pressure_delta = (

            exit_snapshot["pressure_delta"]

            -

            entry_snapshot["pressure_delta"]

        )

        exhaustion_delta = (

            exit_snapshot["exhaustion_score"]

            -

            entry_snapshot["exhaustion_score"]

        )

        if (
            velocity_delta > 0
            and
            pressure_delta > 0
            and
            exhaustion_delta <= 0
        ):

            lifecycle = "EXPANDING"
        
        elif (
            velocity_delta < 0
            and
            pressure_delta < 0

        ):

            lifecycle = "COLLAPSING"

        elif exhaustion_delta > 0.30:

            lifecycle = "EXHAUSTING"
            
        else:

            lifecycle = "STABLE"   

        energy_lifecycle = lifecycle

        pnl = float(
            row["pnl"]
        )

        if pnl > 0:

            trade_result = "WIN"

        elif pnl < 0:

            trade_result = "LOSS"

        else:

            trade_result = "BREAKEVEN"

        trade_quality = (

            calculate_trade_quality(

                row["confidence"],

                entry_snapshot["velocity"],

                entry_snapshot["pressure_delta"],

                pnl

            )

        )

        entry_grade = (

            calculate_entry_grade(

                trade_quality

            )

        )

        market_support = (

            calculate_market_support(

                entry_snapshot["velocity"],

                exit_snapshot["velocity"],

                entry_snapshot["pressure_delta"],

                exit_snapshot["pressure_delta"]

            )

        )

        exit_quality = (

            calculate_exit_quality(

                pnl,

                entry_snapshot["velocity"],

                exit_snapshot["velocity"],

                exit_snapshot["exhaustion_score"]

            )

        )

        energy_state = (

            calculate_energy_state(

                entry_snapshot["velocity"],

                entry_snapshot["pressure_delta"],

                entry_snapshot["exhaustion_score"],

                entry_snapshot["chaos_regime"]

            )

        )

        trade_lifecycle = (

            get_trade_lifecycle(

                row["hold_minutes"]

            )
        )
        
        cursor.execute(
            """
            INSERT INTO trade_summary(

                position_ticket,

                entry_time,
                exit_time,

                symbol,
                direction,
                session_name,

                entry_price,
                exit_price,

                confidence,

                entry_velocity,
                entry_pressure,

                hold_minutes,

                pnl,

                trade_result,

                exit_reason,

                entry_range_expansion,
                entry_volatility_shift,
                entry_exhaustion_score,
                entry_chaos_regime,

                exit_velocity,
                exit_pressure,
                exit_range_expansion,
                exit_volatility_shift,
                exit_exhaustion_score,
                exit_chaos_regime,

                trade_quality,
                entry_grade,
                market_support,
                exit_quality,
                energy_state,

                model_version,

                exit_confidence,

                processed_at,

                trade_lifecycle,

                velocity_delta,
                pressure_delta,
                exhaustion_delta,

                energy_lifecycle

            )

            VALUES(

                %s,%s,%s,
                %s,%s,%s,
                %s,%s,
                %s,
                %s,%s,
                %s,
                %s,
                %s,
                %s,

                %s,%s,%s,%s,

                %s,%s,%s,%s,%s,%s,

                %s,%s,%s,%s,%s,

                %s,

                %s,

                NOW(),

                %s,

                %s,%s,%s,

                %s

            )
            """,
            (

                row["position_ticket"],

                row["entry_time"],
                row["exit_time"],

                row["symbol"],
                row["direction"],
                row["session_name"],

                row["entry_price"],
                row["exit_price"],

                row["confidence"],

                row["entry_velocity"],
                row["entry_pressure"],

                row["hold_minutes"],

                row["pnl"],

                trade_result,

                row["exit_reason"],

                entry_snapshot["range_expansion"],
                entry_snapshot["volatility_shift"],
                entry_snapshot["exhaustion_score"],
                entry_snapshot["chaos_regime"],

                exit_snapshot["velocity"],
                exit_snapshot["pressure_delta"],
                exit_snapshot["range_expansion"],
                exit_snapshot["volatility_shift"],
                exit_snapshot["exhaustion_score"],
                exit_snapshot["chaos_regime"],

                trade_quality,

                entry_grade,

                market_support,

                exit_quality,

                energy_state,

                "AFR_V1",

                exit_snapshot["confidence"],

                trade_lifecycle,

                velocity_delta,

                pressure_delta,

                exhaustion_delta,

                energy_lifecycle

            )
        )

        cursor.execute(
            """
            UPDATE closed_trades

            SET processed = true

            WHERE id = %s
            """,
            (
                row["id"],
            )
        )

        print()

        print(
            "[SUMMARY CREATED]"
        )

        print(
            f"Ticket : "
            f"{row['position_ticket']}"
        )

        print(
            f"Trade Quality : "
            f"{trade_quality}"
        )

        print(
            f"Entry Grade : "
            f"{entry_grade}"
        )

        print(
            f"Energy : "
            f"{energy_state}"
        )

        print(
            f"Result : "
            f"{trade_result}"
        )

    conn.commit()

    cursor.close()

    conn.close()

 # =====================================

 # MAIN LOOP

 # =====================================

print()

print(
"=" * 50
)

print(
"AFR SUMMARY ENGINE V2"
)

print(
"=" * 50
)

LOOP_INTERVAL = 30

success_count = 0

error_count = 0

while True:

    try:

        process_trade_summary()

        success_count += 1

        print()

        print(
            f"[HEALTH] "
            f"success={success_count} "
            f"error={error_count}"
        )

    except KeyboardInterrupt:

        print()

        print(
            "[STOPPED]"
        )

        break

    except Exception as e:

        traceback.print_exc()

        print()

        print(
            "=" * 50
        )

        print(
            "[SUMMARY ERROR]"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "=" * 50
        )

    try:

        conn = psycopg2.connect(
            **DB_CONFIG
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_logs(

                id SERIAL PRIMARY KEY,

                service_name VARCHAR(50),

                level VARCHAR(20),

                message TEXT,

                created_at TIMESTAMP DEFAULT NOW()

            )
            """
        )

        cursor.execute(
            """
            INSERT INTO system_logs(

                service_name,

                level,

                message

            )

            VALUES(

                %s,
                %s,
                %s

            )
            """,
            (

                "summary.py",

                "ERROR",

                str(e)

            )
        )

        conn.commit()

        cursor.close()

        conn.close()

    except Exception:

        pass

time.sleep(
    LOOP_INTERVAL
)
