import asyncio

from config.TRADING_CONFIG import STRAT_1_EXEC_HR, STRAT_1_EXEC_MIN, STRAT_1_EXEC_SEC, \
    STRAT_1_BET_SIZE
from config.TRADING_CONFIG import STRAT_2_EXEC_HR, STRAT_2_EXEC_MIN, STRAT_2_EXEC_SEC, \
    STRAT_2_BET_SIZE
from facade.algo_strat_1_exec_ma import Strat_1_TradingService
from facade.algo_strat_2_exec_ma import Strat_2_TradingService


if __name__ == '__main__':
    async def main():
        strat_1_algo = Strat_1_TradingService.execute_strategy(
            STRAT_1_EXEC_HR, STRAT_1_EXEC_MIN,
            STRAT_1_EXEC_SEC, STRAT_1_BET_SIZE)
        strat_2_algo = Strat_2_TradingService.execute_strategy(
            STRAT_2_EXEC_HR, STRAT_2_EXEC_MIN,
            STRAT_2_EXEC_SEC, STRAT_2_BET_SIZE)

        task_list = [strat_1_algo, strat_2_algo]
        await asyncio.gather(*task_list)

    asyncio.run(main())