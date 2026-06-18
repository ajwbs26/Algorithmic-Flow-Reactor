import psycopg2

def log_error(
    module,
    message
):

    try:

        conn = psycopg2.connect(

            host="100.93.173.69",

            database="postgres",

            user="postgres",

            password="00000",

            port="5432"
        )

        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO afr_system_log (

            timestamp,

            level,

            module,

            message

        )

        VALUES (

            NOW(),

            'ERROR',

            %s,

            %s

        )

        """, (

            module,

            message
        ))

        conn.commit()

        cursor.close()

        conn.close()

    except:

        pass