import psycopg2

DB_CONFIG = {

    "host": "100.93.173.69",

    "database": "postgres",

    "user": "postgres",

    "password": "00000",

    "port": "5432"
}


# =====================================
# OPEN TRADE
# =====================================

def log_open_trade(

    position_ticket,

    entry_time,

    symbol,

    direction,

    entry_price,

    confidence,

    entry_velocity,

    entry_pressure,

    session_name,

    trade_status="OPEN"

):

    try:

        conn = psycopg2.connect(
            **DB_CONFIG
        )

        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO closed_trades (

            position_ticket,

            entry_time,

            symbol,

            direction,

            entry_price,

            confidence,

            entry_velocity,

            entry_pressure,

            session_name,

            trade_status

        )

        VALUES (

            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s

        )

        """, (

            int(position_ticket),

            entry_time,

            symbol,

            direction,

            float(entry_price),

            float(confidence),

            float(entry_velocity),

            float(entry_pressure),

            session_name,

            trade_status

        ))

        conn.commit()

        cursor.close()

        conn.close()

        print(
            "[TRADE OPEN SAVED]"
        )

    except Exception as e:

        print(
            f"[TRADE OPEN ERROR] {e}"
        )


# =====================================
# CLOSE TRADE
# =====================================

def update_closed_trade(

    position_ticket,

    exit_time,

    exit_price,

    pnl,

    exit_reason

):

    try:

        conn = psycopg2.connect(
            **DB_CONFIG
        )

        cursor = conn.cursor()

        cursor.execute("""

        UPDATE closed_trades

        SET

            exit_time=%s,

            exit_price=%s,

            pnl=%s,

            exit_reason=%s,

            trade_status='CLOSED'

        WHERE

            position_ticket=%s

        """, (

            exit_time,

            float(exit_price),

            float(pnl),

            exit_reason,

            int(position_ticket)

        ))

        conn.commit()

        cursor.close()

        conn.close()

        print(
            "[TRADE UPDATED]"
        )

    except Exception as e:

        print(
            f"[TRADE UPDATE ERROR] {e}"
        )