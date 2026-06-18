import psycopg2

DB_CONFIG = {

    "host": "100.93.173.69",

    "database": "postgres",

    "user": "postgres",

    "password": "00000",

    "port": "5432"
}


def log_trade_event(

    ticket,

    symbol,

    direction,

    price,

    confidence,

    session_name,

    message

):

    try:

        conn = psycopg2.connect(
            **DB_CONFIG
        )

        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO trade_events (

            event_time,

            ticket,

            symbol,

            direction,

            price,

            confidence,

            session_name,

            message

        )

        VALUES (

            NOW(),

            %s,%s,%s,%s,

            %s,%s,%s

        )

        """,

        (

            ticket,

            symbol,

            direction,

            price,

            float(confidence),

            session_name,

            message

        ))

        conn.commit()

        cursor.close()

        conn.close()

        print(
            "[TRADE EVENT] saved"
        )

    except Exception as e:

        print(
            f"[TRADE EVENT ERROR] {e}"
        )