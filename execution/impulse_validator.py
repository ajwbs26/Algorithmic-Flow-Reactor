def validate_impulse(

    velocity,
    pressure,
    range_expansion,
    confidence

):

    score = 0


    # =====================================
    # CONFIDENCE
    # =====================================

    if confidence >= 0.80:

        score += 1


    # =====================================
    # VELOCITY
    # =====================================

    if abs(velocity) >= 0.30:

        score += 1


    # =====================================
    # PRESSURE
    # =====================================

    if abs(pressure) >= 0.05:

        score += 1


    # =====================================
    # RANGE EXPANSION
    # =====================================

    if range_expansion >= 1.00:

        score += 1


    # =====================================
    # FINAL SCORE
    # =====================================

    return score >= 3