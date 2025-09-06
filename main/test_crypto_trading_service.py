from typing import Dict

import ccxt
import time
import pytz
import pandas as pd
from datetime import date, timedelta, datetime, tzinfo
from loguru import logger
from ccxt.base.exchange import Exchange

from facade.test_crypto_price_data_service import CryptoPriceDataService
from config.TRADING_CONFIG import API_KEY, SECRET_KEY


class CryptoTradingService:
    # const
    symbol: str = 'BTC-PERPETUAL'
    long_r_thres: float
    short_r_thres: float
    # long_r_thres, short_r_thres = -0.04, 0.02
    long_r_thres, short_r_thres = -0.04, 0
    # init
    deribit: Exchange = ccxt.deribit({
        'apiKey': API_KEY,
        'secret': SECRET_KEY
    })
    markets: Dict = deribit.load_markets()
    market: Dict = deribit.market(symbol)


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
                    signal: int = cls.create_signal()
                    cls.create_market_order(signal, bet_size)
                    time.sleep(1)
                    logger.info('End executing strat, UTC time={}', str(datetime.now(tz=pytz.UTC)))
            except:
                pass


    @classmethod
    def create_signal(cls) -> int:
        five_day_millisec: int = 3600 * 24 * 5 * 1000
        t_minus_5_ts: str = cls.deribit.iso8601(cls.deribit.milliseconds() - five_day_millisec)
        bnb_data_df: pd.DataFrame = CryptoPriceDataService.fetch_ohlcv_times_series_df(
            'BNB/USDT', 'binance', '1d', t_minus_5_ts)
        bnb_r_series: pd.Series = bnb_data_df['BNB/USDT_binance_close'].pct_change()

        # check last data point is on today
        last_date: date = bnb_r_series.index[-1].date()
        utc_current_dt: datetime = datetime.now(tz=pytz.UTC)
        utc_current_date: date = utc_current_dt.date()
        if last_date != utc_current_date:
            logger.error('df last date is not today! df last date = {}', str(last_date))
            signal: int = 0
            return signal
        # check 2nd last data point is on ytd
        second_last_date: date = bnb_r_series.index[-2].date()
        ytd_date: date = utc_current_date - timedelta(days=1)
        if second_last_date != ytd_date:
            logger.error('df 2nd last date is not ytd! df 2nd last date = {}', str(second_last_date))
            signal = 0
            return signal
        # create signal from return
        bnb_r_t_minus_one: float = bnb_r_series.iloc[-2]
        if pd.isna(bnb_r_t_minus_one):
            logger.error('r_t-1 is NaN!')
            signal = 0
            return signal
        if bnb_r_t_minus_one < cls.long_r_thres:
            signal = 1
        elif bnb_r_t_minus_one > cls.short_r_thres:
            signal = -1
        else:
            signal = 0
        logger.debug('Model Signal = {}', str(signal))

        print('signal: ', signal)
        return signal


    @classmethod
    def create_market_order(cls, signal: int = 0, bet_size: float = 10) -> None:
        # chk original acct position
        position_info_dict: Dict = cls.deribit.fetch_positions([cls.symbol])[0]['info']
        side: str = position_info_dict.get('direction')
        position_size: float = float(position_info_dict.get('size'))
        time.sleep(0.05)  # rate limit for deribit is 20 ms

        # # execute mkt order
        if signal == 1:
            if side == 'sell' and position_size == bet_size:
                flat_order: Dict = cls.deribit.create_order(cls.symbol, 'market', 'sell',
                                                          bet_size, None)
                time.sleep(0.05)
                buy_order: Dict = cls.deribit.create_order(cls.symbol, 'market', 'buy',
                                                           bet_size, None)
            if side == 'zero' and position_size == 0:
                buy_order = cls.deribit.create_order(cls.symbol, 'market', 'buy',
                                                     bet_size, None)
        elif signal == -1:
            if side == 'buy' and position_size == bet_size:
                flat_order = cls.deribit.create_order(cls.symbol, 'market', 'sell',
                                                    bet_size, None)
                time.sleep(0.05)
                sell_order: Dict = cls.deribit.create_order(cls.symbol, 'market', 'sell',
                                                          bet_size, None)
            if side == 'zero' and position_size == 0:
                sell_order = cls.deribit.create_order(cls.symbol, 'market', 'sell',
                                                    bet_size, None)
        elif signal == 0:
            if side == 'buy' and position_size == bet_size:
                flat_order = cls.deribit.create_order(cls.symbol, 'market', 'sell',
                                                    bet_size, None)
            if side == 'sell' and position_size == bet_size:
                flat_order = cls.deribit.create_order(cls.symbol, 'market', 'buy',
                                                    bet_size, None)
        time.sleep(0.05)

        # chk acct after trading
        position_info_dict = cls.deribit.fetch_positions([cls.symbol])[0]['info']
        side = position_info_dict.get('direction')
        position_size = float(position_info_dict.get('size'))
        logger.info('Account position after trading: side = {}, position size = {}',
                    side, str(position_size))
        time.sleep(0.05)
        usdt_acct_bal: float = cls.deribit.fetch_balance().get('USDT').get('total')
        logger.info('USDT Account balance = {}', str(usdt_acct_bal))
        return

#from facade.test_crypto_trading_service import CryptoTradingService

if __name__ == '__main__':
    CryptoTradingService.execute_strategy(15, 59, 0)
    # CryptoTradingService.create_market_order(0, 10)
    # CryptoTradingService.create_signal()
