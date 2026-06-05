import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier
)

from sklearn.metrics import (

    classification_report,

    confusion_matrix
)

from sklearn.model_selection import (
    train_test_split
)


print()
print("=== AFR TRAINING ENGINE ===")
print()


# =====================================
# LOAD DATASET
# =====================================

df = pd.read_csv(
    "data/processed/afr_dataset_v4.csv"
)


# =====================================
# CLEAN
# =====================================

df = df.replace(

    [np.inf, -np.inf],

    np.nan
)

df = df.dropna()

df = df.reset_index(
    drop=True
)


print(
    f"[ROWS] {len(df)}"
)


# =====================================
# FEATURES
# =====================================

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
# FEATURE MATRIX
# =====================================

X = df[
    FEATURE_COLUMNS
]

y = df["state"]


# =====================================
# SPLIT
# =====================================

X_train, X_test, y_train, y_test = (

    train_test_split(

        X,

        y,

        test_size=0.2,

        shuffle=False
    )
)


print()

print(
    f"[TRAIN] {len(X_train)}"
)

print(
    f"[TEST] {len(X_test)}"
)


# =====================================
# MODEL
# =====================================

model = RandomForestClassifier(

    n_estimators=1000,

    max_depth=15,

    min_samples_leaf=5,

    random_state=42,

    n_jobs=-1,

    class_weight="balanced_subsample"
)

# =====================================
# TRAIN
# =====================================

print()

print(
    "[INFO] training AFR..."
)

model.fit(

    X_train,

    y_train
)


# =====================================
# PREDICT
# =====================================

predictions = model.predict(
    X_test
)

probabilities = model.predict_proba(
    X_test
)


# =====================================
# FEATURE IMPORTANCE
# =====================================

importance_df = pd.DataFrame({

    "feature":
        FEATURE_COLUMNS,

    "importance":
        model.feature_importances_
})

importance_df = (

    importance_df

    .sort_values(

        by="importance",

        ascending=False
    )
)


print()
print("=== FEATURE IMPORTANCE ===")
print()

print(
    importance_df
)


# =====================================
# REPORT
# =====================================

print()
print("=== CLASSIFICATION REPORT ===")
print()

print(

    classification_report(

        y_test,

        predictions
    )
)


# =====================================
# CONFUSION MATRIX
# =====================================

print()
print("=== CONFUSION MATRIX ===")
print()

print(

    confusion_matrix(

        y_test,

        predictions
    )
)


# =====================================
# CONFIDENCE
# =====================================

max_probabilities = np.max(

    probabilities,

    axis=1
)


print()
print("=== CONFIDENCE ===")
print()

print(
    f"[AVG] {max_probabilities.mean():.4f}"
)

print(
    f"[MAX] {max_probabilities.max():.4f}"
)

print(
    f"[MIN] {max_probabilities.min():.4f}"
)

# =====================================
# STATE DISTRIBUTION
# =====================================

print()
print("=== STATE DISTRIBUTION ===")
print()

print(
    df["state"].value_counts()
)

print()

print(
    df["state"].value_counts(
        normalize=True
    )
)
# =====================================
# SAVE MODEL
# =====================================

joblib.dump(

    model,

    "model/afr_model.pkl"
)


joblib.dump(

    FEATURE_COLUMNS,

    "model/feature_columns.pkl"
)


print()

print(
    "[OK] AFR model saved"
)

print(
    "[OK] feature columns saved"
)
