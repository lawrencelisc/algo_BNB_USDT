from typing import List, Union, Dict, Optional

import ccxt, time, pandas
from loguru import logger
from ccxt.base.exchange import Exchange


class CryptoPriceDataService:
    # const
    _TIMEFRAME_TIMESTAMP_DICT = {'1d': 86400000, '1h': 3600000, '30m': 1800000,
                                 '15m': 900000, '5m': 300000, '1m': 60000}
    _COLUMN_NAME_LIST: List[str] = ['open', 'high', 'low', 'close', 'volume']
    # init
    binance: Exchange = ccxt.binance()
    binanceusdm: Exchange = ccxt.binanceusdm()
    kucoin: Exchange = ccxt.kucoin()
    huobi: Exchange = ccxt.huobi()
    lbank: Exchange = ccxt.lbank()
    exchange_dict: Dict = {'binance': binance, 'binanceusdm': binanceusdm,
                           'kucoin': kucoin, 'huobi': huobi, 'lbank': lbank}

    def __init__(self):
        return

    @classmethod
    def fetch_ohlcv_times_series_df(cls, symbol: str = 'BTC/USDT', exchange_name: str = 'binance',
                                    timeframe: str = '1d', date_since: str = '2020-07-01T00:00:00Z') \
            -> Optional[pandas.DataFrame]:
        exchange: Optional[Exchange] = cls.exchange_dict.get(exchange_name)
        if exchange is None:
            logger.error('Input exchange is not available!, exchange_name={}', exchange_name)
            return
        timestamp_int_since: int = exchange.parse8601(date_since)
        all_candle_list: List[List[Union[int, float]]] = exchange.fetch_ohlcv(
            symbol, timeframe, since=timestamp_int_since, limit=exchange.rateLimit)
        if len(all_candle_list) == 0:
            logger.error('Invalid start date, date={}', date_since)
            return None

        # Binance O and C time: 00:00:00 and 23:59:59
        last_timestamp_int_since: int = all_candle_list[-1][0]
        while exchange.milliseconds() - last_timestamp_int_since >= cls._TIMEFRAME_TIMESTAMP_DICT.get(timeframe):
            time.sleep(exchange.rateLimit / 1000)
            later_timestamp_since: int = last_timestamp_int_since + cls._TIMEFRAME_TIMESTAMP_DICT.get(timeframe)
            candle_list: List[List[Union[int, float]]] = exchange.fetch_ohlcv(
                symbol, timeframe, since=later_timestamp_since, limit=exchange.rateLimit)
            # to handle exchange maintanence time data point
            while len(candle_list) == 0:
                time.sleep(exchange.rateLimit / 1000)
                later_timestamp_since: int = later_timestamp_since + cls._TIMEFRAME_TIMESTAMP_DICT.get(timeframe)
                candle_list: List[List[Union[int, float]]] = exchange.fetch_ohlcv(
                    symbol, timeframe, since=later_timestamp_since, limit=exchange.rateLimit)
            all_candle_list.extend(candle_list)
            logger.info('Last timestamp fetched, ts={}', exchange.iso8601(all_candle_list[-1][0]))
            last_timestamp_int_since = all_candle_list[-1][0]

        candlestick_df: pandas.DataFrame = pandas.DataFrame.from_records(all_candle_list)
        column_name_list: List[str] = ['timestamp_int'] + [
            symbol + '_' + exchange_name + '_' + name for name in cls._COLUMN_NAME_LIST]
        candlestick_df.columns = column_name_list
        candlestick_df['timestamp'] = candlestick_df['timestamp_int'].apply(
            lambda x: pandas.to_datetime(exchange.iso8601(x)))
        candlestick_df = candlestick_df.set_index('timestamp')
        candlestick_df = candlestick_df.drop(columns=['timestamp_int'])
        return candlestick_df
