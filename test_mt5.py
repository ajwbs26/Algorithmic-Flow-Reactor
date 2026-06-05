import MetaTrader5 as mt5


print()
print("=== TEST MT5 ===")
print()


# =====================================
# INIT
# =====================================

if not mt5.initialize():

    print(
        "[ERROR] initialize failed"
    )

    quit()


print(
    "[OK] MT5 connected"
)


# =====================================
# ACCOUNT INFO
# =====================================

account = mt5.account_info()

print()
print(account)


# =====================================
# SYMBOL INFO
# =====================================

symbol = mt5.symbol_info(
    "XAUUSD"
)

print()
print(symbol)


# =====================================
# LAST TICK
# =====================================

tick = mt5.symbol_info_tick(
    "XAUUSD"
)

print()
print(tick)


mt5.shutdown()