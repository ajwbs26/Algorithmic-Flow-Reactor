import os
import joblib
import psycopg2
import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier
)

from sklearn.metrics import (
    r2_score,
    accuracy_score
)

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
# SETTINGS
# =====================================

MIN_TRADES = 30

MODEL_DIR = "models"

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

# =====================================
# LOAD DATA
# =====================================

def load_trade_summary():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    query = """

    SELECT *

    FROM trade_summary

    WHERE

        trade_quality IS NOT NULL

        AND

        entry_grade IS NOT NULL

    """

    df = pd.read_sql(
        query,
        conn
    )

    conn.close()

    return df

# =====================================
# ENTRY GRADE MAPPING
# =====================================

GRADE_MAP = {

    "D": 0,

    "C": 1,

    "B": 2,

    "A": 3,

    "A+": 4

}

# =====================================
# PREPARE DATA
# =====================================

def prepare_data(df):

    df = df.copy()

    df["entry_grade_num"] = (
        df["entry_grade"]
        .map(GRADE_MAP)
    )

    df["velocity_delta"] = (

        df["exit_velocity"]

        -

        df["entry_velocity"]

    )

    df["pressure_delta"] = (

        df["exit_pressure"]

        -

        df["entry_pressure"]

    )

    df["exhaustion_delta"] = (

        df["exit_exhaustion_score"]

        -

        df["entry_exhaustion_score"]

    )

    features = [

        "confidence",
        "entry_velocity",
        "entry_pressure",
        "entry_range_expansion",
        "entry_volatility_shift",
        "entry_exhaustion_score",
        "exit_velocity",
        "exit_pressure",
        "exit_range_expansion",
        "exit_volatility_shift",
        "exit_exhaustion_score",
        "exit_confidence",
        "velocity_delta",
        "pressure_delta",
        "exhaustion_delta"

    ]

    X = df[
        features
    ].fillna(0)

    y_quality = df[
        "trade_quality"
    ]

    y_grade = df[
        "entry_grade_num"
    ]

    return (

        X,

        y_quality,

        y_grade

    )

# =====================================
# TRAIN
# TRADE QUALITY MODEL
# =====================================

def train_trade_quality(

    X,

    y

):

    X_train,\
    X_test,\
    y_train,\
    y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42

    )

    model = RandomForestRegressor(

        n_estimators=300,

        max_depth=8,

        min_samples_leaf=2,

        random_state=42,

        n_jobs=-1

    )

    model.fit(

        X_train,

        y_train

    )

    pred = model.predict(

        X_test

    )

    score = r2_score(

        y_test,

        pred

    )

    return (

        model,

        score

    )

# =====================================
# TRAIN
# ENTRY GRADE MODEL
# =====================================

def train_entry_grade(

    X,

    y

):

    X_train,\
    X_test,\
    y_train,\
    y_test = train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42

    )

    model = RandomForestClassifier(

        n_estimators=300,

        max_depth=8,

        min_samples_leaf=2,

        random_state=42,

        n_jobs=-1

    )

    model.fit(

        X_train,

        y_train

    )

    pred = model.predict(

        X_test

    )

    score = accuracy_score(

        y_test,

        pred

    )

    return (

        model,

        score

    )

def get_new_model_version():

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT model_version
        FROM ai_models
        ORDER BY id DESC
        LIMIT 1
        """
    )

    last_model = cursor.fetchone()

    cursor.close()
    conn.close()

    if last_model is None:

        return "AFR_V1"

    last_version = int(
        last_model[0]
        .replace(
            "AFR_V",
            ""
        )
    )

    return (
        f"AFR_V{last_version + 1}"
    )

# =====================================
# SAVE AI MODELS
# =====================================

def save_ai_models(

    model_version,

    trade_count,

    quality_score,

    grade_score,

    quality_model,

    feature_names

):

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    cursor = conn.cursor()

    importance_map = {}

    for feature, importance in zip(

        feature_names,

        quality_model.feature_importances_

    ):

        importance_map[
            feature
        ] = round(
            float(
                importance
            ),
            4
        )

    cursor.execute(
        """
        INSERT INTO ai_models(

            model_version,

            trade_count,

            trade_quality_score,

            entry_grade_score,

            active_model,

            confidence_importance,

            entry_velocity_importance,

            entry_pressure_importance,

            range_expansion_importance,

            volatility_shift_importance,

            exhaustion_importance,

            chaos_regime_importance,

            velocity_delta_importance,

            pressure_delta_importance,

            exhaustion_delta_importance,

            created_at

        )

        VALUES(

            %s,%s,%s,%s,
            %s,

            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,

            NOW()

        )
        """,
        (

            model_version,

            trade_count,

            quality_score,

            grade_score,

            True,

            importance_map.get(
                "confidence",
                0
            ),

            importance_map.get(
                "entry_velocity",
                0
            ),

            importance_map.get(
                "entry_pressure",
                0
            ),

            importance_map.get(
                "entry_range_expansion",
                0
            ),

            importance_map.get(
                "entry_volatility_shift",
                0
            ),

            importance_map.get(
                "entry_exhaustion_score",
                0
            ),

            importance_map.get(
                "entry_chaos_regime",
                0
            ),

            importance_map.get(
                "velocity_delta",
                0
            ),

            importance_map.get(
                "pressure_delta",
                0
            ),

            importance_map.get(
                "exhaustion_delta",
                0
            )

        )
    )

    conn.commit()

    cursor.close()

    conn.close()

# =====================================
# SAVE AI LEARNING LOG
# =====================================

def save_ai_learning_log(

    model_version,

    quality_score,

    grade_score

):

    conn = psycopg2.connect(
        **DB_CONFIG
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            model_version,

            trade_quality_score,

            entry_grade_score

        FROM ai_models

        WHERE model_version <> %s

        ORDER BY id DESC

        LIMIT 1
        """,
        (
            model_version,
        )
    )

    previous = cursor.fetchone()

    if previous is None:

        decision = "INITIAL"

        prev_version = None

        prev_quality = 0

        prev_accuracy = 0

        improvement_pct = 0

    else:

        prev_version = previous[0]

        prev_quality = previous[1]

        prev_accuracy = previous[2]

        improvement_pct = round(

            (
                quality_score
                -
                prev_quality
            )

            * 100,

            2

        )

        if quality_score > prev_quality:

            decision = "PROMOTED"

        else:

            decision = "REJECTED"

    cursor.execute(
        """
        INSERT INTO ai_learning_log(

            model_version,

            previous_version,

            previous_quality,

            current_quality,

            previous_accuracy,

            current_accuracy,

            improvement_pct,

            decision,

            notes,

            created_at

        )

        VALUES(

            %s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,
            NOW()

        )
        """,
        (

            model_version,

            prev_version,

            prev_quality,

            quality_score,

            prev_accuracy,

            grade_score,

            improvement_pct,

            decision,

            f"Compared {prev_version} vs {model_version}"

        )
    )

    conn.commit()

    cursor.close()

    conn.close()

# =====================================
# SAVE MODELS
# =====================================
def save_models(

        quality_model,

        grade_model

):

    joblib.dump(

        quality_model,

        os.path.join(

            MODEL_DIR,

            "trade_quality_model.joblib"

        )

    )

    joblib.dump(

        grade_model,

        os.path.join(

            MODEL_DIR,

            "entry_grade_model.joblib"

        )

    )

# =====================================
# FEATURE IMPORTANCE
# =====================================

def print_feature_importance(

    model,

    feature_names

):

    print()

    print(
        "=" * 50
    )

    print(
        "FEATURE IMPORTANCE"
    )

    print(
        "=" * 50
    )

    importance = list(

        zip(

            feature_names,

            model.feature_importances_

        )

    )

    importance.sort(

        key=lambda x: x[1],

        reverse=True

    )

    for name, score in importance:

        print(

            f"{name:<30}"

            f"{score:.4f}"

        )

# =====================================
# MAIN
# =====================================

def main():

    print()

    print(
        "=" * 50
    )

    print(
        "AFR RETRAIN ENGINE V1"
    )

    print(
        "=" * 50
    )

    df = load_trade_summary()

    trade_count = len(
        df
    )

    print()

    print(
        f"Trades Found : "
        f"{trade_count}"
    )

    if trade_count < MIN_TRADES:

        print()

        print(
            "[SKIP]"
        )

        print(
            f"Minimum "
            f"{MIN_TRADES} trades "
            f"required"
        )

        return

    X,\
    y_quality,\
    y_grade = prepare_data(
        df
    )

    quality_model,\
    quality_score = (

        train_trade_quality(

            X,

            y_quality

        )

    )

    grade_model,\
    grade_score = (

        train_entry_grade(

            X,

            y_grade

        )

    )

    model_version = (
        get_new_model_version()
    )

    feature_names = [

        "confidence",

        "entry_velocity",
        "entry_pressure",

        "entry_range_expansion",
        "entry_volatility_shift",

        "entry_exhaustion_score",

        "entry_chaos_regime",

        "exit_velocity",
        "exit_pressure",

        "exit_range_expansion",
        "exit_volatility_shift",

        "exit_exhaustion_score",

        "exit_confidence",

        "velocity_delta",
        "pressure_delta",
        "exhaustion_delta"

    ]

    save_models(

        quality_model,

        grade_model

    )

    save_ai_models(

        model_version,

        trade_count,

        quality_score,

        grade_score,

        quality_model,

        feature_names

    )

    save_ai_learning_log(

        model_version,

        quality_score,

        grade_score

    )

    print()

    print(
        "=" * 50
    )

    print(
        "TRAINING RESULT"
    )

    print(
        "=" * 50
    )

    print()

    print(
        f"Trade Quality R2 : "
        f"{quality_score:.4f}"
    )

    print(
        f"Entry Grade Accuracy : "
        f"{grade_score:.4f}"
    )

    feature_names = [

        "confidence",

        "entry_velocity",
        "entry_pressure",

        "entry_range_expansion",
        "entry_volatility_shift",

        "entry_exhaustion_score",

        "entry_chaos_regime",

        "exit_velocity",
        "exit_pressure",

        "exit_range_expansion",
        "exit_volatility_shift",

        "exit_exhaustion_score",

        "exit_confidence",

        "velocity_delta",
        "pressure_delta",
        "exhaustion_delta"

    ]

    print_feature_importance(

        quality_model,

        feature_names

    )

    print()

    print(
        "[SUCCESS]"
    )

    print(
        "Models saved"
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
            "[RETRAIN ERROR]"
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )