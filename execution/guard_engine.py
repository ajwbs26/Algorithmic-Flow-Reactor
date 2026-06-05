def guard_check(

    confidence,
    chaos,
    spread,
    cooldown_active

):
    guard_ok = guard_check(
    confidence,
    chaos,
    spread,
    cooldown_active
)

    if cooldown_active:
        return False

    if chaos == 1:
        return False

    if spread > 0.30:
        return False

    if confidence < 0.90:
        return False

    return True

    if guard_ok:

        guard_pass_count += 1