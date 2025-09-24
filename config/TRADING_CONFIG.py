# API bybit info
API_KEY: str = 'D3QhDAJfUgEh4Rs24X'
SECRET_KEY: str = 'G26JWqTnjUoZAGKhyD3ObEqqqSUm8HtaDEpe'

# strategy parameter
COIN_1_SYMBOL: str = 'SOL'
# coin strategy 1 rolling day in MA: float = 30
COIN_1_ROL_DAY: float = 30
# coin strategy 1 LONG threshold in MA: float = 0.05
COIN_1_LONG_THRES: float = 0.05

COIN_2_SYMBOL: str = 'ETH'
# coin strategy 2 rolling day in MA: float = 20
COIN_2_ROL_DAY: float = 20
# coin strategy 1 LONG threshold in MA: float = 0.02
COIN_2_LONG_THRES: float = 0.02

# execution parameter
STRAT_1_EXEC_HR: int = 2
STRAT_1_EXEC_MIN: int = 00
STRAT_1_EXEC_SEC: int = 00
STRAT_1_BET_SIZE: float = 2

STRAT_2_EXEC_HR: int = 2
STRAT_2_EXEC_MIN: int = 00
STRAT_2_EXEC_SEC: int = 25
STRAT_2_BET_SIZE: float = 0.05
