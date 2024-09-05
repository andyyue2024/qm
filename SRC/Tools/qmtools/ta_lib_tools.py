import numpy as np
import pandas as pd
from functools import reduce
import talib


def SMA_CN(close, timeperiod):
    return reduce(lambda x, y: ((timeperiod - 1) * x + y) / timeperiod, close)


def RSI_CN(close, timeperiod):
    diff = map(lambda x, y: x - y, close[1:], close[:-1])
    diffGt0 = map(lambda x: 0 if x < 0 else x, diff)
    diffABS = map(lambda x: abs(x), diff)
    diff = np.array(diff)
    diffGt0 = np.array(diffGt0)
    diffABS = np.array(diffABS)
    diff = np.append(diff[0], diff)
    diffGt0 = np.append(diffGt0[0], diffGt0)
    diffABS = np.append(diffABS[0], diffABS)
    rsi = map(lambda x: SMA_CN(diffGt0[:x], timeperiod) / SMA_CN(diffABS[:x], timeperiod) * 100,
              range(1, len(diffGt0) + 1))

    return np.array(rsi)


def KDJ_CN(high, low, close, fastk_period, slowk_period, fastd_period):
    kValue, dValue = talib.STOCHF(high, low, close, fastk_period, fastd_period=1, fastd_matype=0)

    kValue = np.array(map(lambda x: SMA_CN(kValue[:x], slowk_period), range(1, len(kValue) + 1)))
    dValue = np.array(map(lambda x: SMA_CN(kValue[:x], fastd_period), range(1, len(kValue) + 1)))

    jValue = 3 * kValue - 2 * dValue

    func = lambda arr: np.array([0 if x < 0 else (100 if x > 100 else x) for x in arr])

    kValue = func(kValue)
    dValue = func(dValue)
    jValue = func(jValue)
    return kValue, dValue, jValue


def MACD_CN(close, fastperiod=12, slowperiod=26, signalperiod=9):
    macdDIFF, macdDEA, macd = talib.MACDEXT(close, fastperiod=fastperiod, fastmatype=1, slowperiod=slowperiod,
                                            slowmatype=1, signalperiod=signalperiod, signalmatype=1)
    macd = macd * 2
    return macdDIFF, macdDEA, macd


def EMA(S: np.ndarray, N: int = 120) -> np.ndarray:
    '''
    指数移动平均,为了精度 S>4*N  EMA至少需要120周期
    alpha=2/(span+1)

    Args:
        S (np.ndarray): 时间序列
        N (int): 指标周期

    Returns:
        np.ndarray: EMA
    '''
    return pd.Series(S).ewm(span=N, adjust=False).mean().values


def MACD(CLOSE: np.ndarray,
         SHORT: int = 12,
         LONG: int = 26,
         M: int = 9) -> tuple:
    '''计算MACD
    EMA的关系，S取120日

    Args:
        CLOSE (np.ndarray): 收盘价时间序列
        SHORT (int, optional): ema 短周期. Defaults to 12.
        LONG (int, optional): ema 长周期. Defaults to 26.
        M (int, optional): macd 平滑周期. Defaults to 9.

    Returns:
        tuple: _description_
    '''
    DIF = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG)
    DEA = EMA(DIF, M)
    MACD = (DIF - DEA) * 2
    return DIF, DEA, MACD
