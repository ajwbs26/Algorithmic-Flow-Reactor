import os
import joblib
import psycopg2
import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.preprocessing import StandardScaler

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

    features = [

        "confidence",

        "entry_velocity",
        "entry_pressure",

        "entry_range_expansion",
        "entry_volatility_shift",
        "entry_exhaustion_score",

        "hold_minutes"

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

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X
    )

    return (

        X_scaled,

        y_quality,

        y_grade,

        scaler

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

# =====================================
# SAVE MODELS
# =====================================

def save_models(

    scaler,

    quality_model,

    grade_model

):

    joblib.dump(

        scaler,

        os.path.join(

            MODEL_DIR,

            "scaler.joblib"

        )

    )

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
    y_grade,\
    scaler = prepare_data(
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

    save_models(

        scaler,

        quality_model,

        grade_model

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

        "hold_minutes"

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