import time
import psycopg2
from datetime import datetime
from notifier import send_message

LAST_ALERT = False

while True:

    try:

        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="00000",
            port="5432"
        )

        cur = conn.cursor()

        cur.execute("""

            SELECT MAX(timestamp)

            FROM afr_live_data

        """)

        last_time = cur.fetchone()[0]

        cur.close()
        conn.close()

        seconds = (
            datetime.now()
            - last_time
        ).total_seconds()

        if seconds > 180:

            if not LAST_ALERT:

                send_message(

                    "🚨 VPS WINDOWS OFFLINE\n\n"

                    f"Last Data : {last_time}"
                )

                LAST_ALERT = True

        else:

            LAST_ALERT = False

    except Exception as e:

        print(e)

    time.sleep(60)