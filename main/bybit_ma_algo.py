from typing import Dict

import ccxt
import sys
import time
import pytz
import gc
import pandas as pd

from datetime import date, timedelta, datetime, tzinfo
from loguru import logger
from ccxt.base.exchange import Exchange

from facade.test_crypto_price_data_service import CryptoPriceDataService
from config.TRADING_CONFIG import API_KEY, SECRET_KEY


class CryptoTradingService:
    # const
    symbol: str = 'SOLUSDT'
    leverage: str = '2'  # Set leverage to 2x
    bet_size: float = 1 # Set unit of crypto to trade
    long_thres: float
    rol_day: float
    long_thres, rol_day = 0.05, 30
    # init
    bybit: Exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': SECRET_KEY
    })
    markets: Dict = bybit.load_markets()
    market: Dict = bybit.market(symbol)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)


    def __init__(self):
        return

    @classmethod
    def execute_strategy(cls, exec_hr_int: int = 0, exec_min_int: int = 1,
                         exec_sec_int: int = 0, bet_size: float = 10) -> None:

        while True:
            try:
                utc_current_dt: datetime = datetime.now(tz=pytz.UTC)
                utc_current_hr: int = utc_current_dt.hour
                utc_current_min: int = utc_current_dt.minute
                utc_current_sec: int = utc_current_dt.second
                if utc_current_hr == exec_hr_int and utc_current_min == exec_min_int \
                        and utc_current_sec == exec_sec_int:
                    logger.info('Start executing strat, UTC time={}', str(datetime.now(tz=pytz.UTC)))
                    signal: int = cls.create_signal(cls.long_thres, cls.rol_day)
                    cls.create_market_order(signal, bet_size)  # run order execution
                    time.sleep(1)
                    logger.info('End executing strat, UTC time={}', str(datetime.now(tz=pytz.UTC)))
                    gc.collect()
            except KeyboardInterrupt:
                print('Program stopped by user.')
                sys.exit(0)


    @classmethod
    def create_signal(cls, long_thres: float = 0.05, rol_day: float = 30) -> int:
        day100_millisec: int = 3600 * 24 * 100 * 1000
        t_minus_100_ts: str = cls.bybit.iso8601(cls.bybit.milliseconds() - day100_millisec)
        sol_data_df: pd.DataFrame = CryptoPriceDataService.fetch_ohlcv_times_series_df(
            'SOL/USDC', 'binance', '1d', t_minus_100_ts)
        df: pd.DataFrame = sol_data_df[['SOL/USDC_binance_close']].copy()
        df['ma'] = df['SOL/USDC_binance_close'].rolling(rol_day).mean()
        df['ma_diff'] = df['SOL/USDC_binance_close'] / df['ma'] - 1
        # check last data point is on today
        last_date: date = df.index[-1].date()
        utc_current_dt: datetime = datetime.now(tz=pytz.UTC)
        utc_current_date: date = utc_current_dt.date()
        if last_date != utc_current_date:
            logger.error('df last date is not today! df last date = {}', str(last_date))
            signal: int = 0
            return signal
        # check 2nd last data point is on ytd
        second_last_date: date = df.index[-2].date()
        ytd_date: date = utc_current_date - timedelta(days=1)
        if second_last_date != ytd_date:
            logger.error('df 2nd last date is not ytd! df 2nd last date = {}', str(second_last_date))
            signal = 0
            return signal
        # create signal from return
        coin_t_minus_one: float = df.loc[df.index[-1], 'ma_diff']
        if pd.isna(coin_t_minus_one):
            logger.error('value is NaN!')
            signal = 0
            return signal
        if coin_t_minus_one > cls.long_thres:
            signal = 1
        else:
            signal = 0
        logger.debug('Model (signal) = {}', str(signal))
        logger.debug('Latest ma diff = {}', str(coin_t_minus_one))
        logger.debug('Threshold (long_thres) = {}', str(long_thres))
        return signal


    @classmethod
    def create_market_order(cls, signal: int = 0, bet_size: float = 10) -> None:
        # chk original acct position
        position_info_dict: Dict = cls.bybit.fetch_positions([cls.symbol])[0]['info']
        side: str = position_info_dict.get('side')
        position_size: float = abs(float(position_info_dict.get('size')))
        params = {
            'leverage': cls.leverage
                  }
        usdt_acct_bal: float = cls.bybit.fetch_balance().get('USDT').get('total')
        logger.info('USDT Account balance = {}', str(usdt_acct_bal))

        time.sleep(0.05)  # rate limit for bybit is 20 ms
        # execute mkt order
        if signal == 1:
            if side == 'Buy' and position_size == bet_size:
                logger.info('Account position is active: side = {}, position size = {}',
                            side, str(position_size))
            elif (side == 'None' or side == '') and position_size == 0:
                buy_order: Dict = cls.bybit.create_order(cls.symbol, 'market', 'buy',
                                                         bet_size, params=params)
        elif signal == 0:
            if side == 'Buy' and position_size == bet_size:
                flat_order: Dict = cls.bybit.create_order(cls.symbol, 'market', 'sell',
                                                          bet_size, params=params)
            elif (side == 'None' or side == '') and position_size == 0:
                logger.info('Account position is null: side = {}, position size = {}',
                            side, str(position_size))
        time.sleep(0.05)
        # chk acct after trading
        position_info_dict = cls.bybit.fetch_positions([cls.symbol])[0]['info']
        side = position_info_dict.get('side')
        position_size = float(position_info_dict.get('size'))
        logger.info('Account position after trading: side = {}, position size = {}',
                    side, str(position_size))
        time.sleep(0.05)
        usdt_acct_bal: float = cls.bybit.fetch_balance().get('USDT').get('total')
        logger.info('USDT Account balance = {}', str(usdt_acct_bal))
        return

#from facade.test_crypto_trading_service import CryptoTradingService

if __name__ == '__main__':
    CryptoTradingService.execute_strategy(23, 59, 0)
    # CryptoTradingService.create_signal(0.05, 30)
    # CryptoTradingService.create_market_order(0, CryptoTradingService.bet_size)
