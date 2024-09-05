from datetime import datetime, date
from typing import Any
import numpy as np
import pandas as pd
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market
from sklearn import preprocessing

from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


class GrowthModel(BaseGMModel):

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int = 5):
        super().__init__(index_list, now, top_count)

    def get_target_and_factor_list(self, symbol_list: list) -> list | pd.DataFrame:
        # fields: str | list = None, filters: str = None,
        day_time = get_previous_trading_date("SHSE", self.now)

        df = pd.DataFrame([])
        df["symbol"] = symbol_list
        df["EBITG"] = -999.0
        df["NPG"] = -999.0
        df["TAG"] = -999.0  # MPG取不到，用TAG代替
        df["GPG"] = -999.0
        df["OPG"] = -999.0
        df["OCG"] = -999.0
        # 求出 息税前利润率EBITG
        for number in range(len(symbol_list)):
            try:
                _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list[number],
                                         end_date=day_time,
                                         count=2, fields="EBITMARGIN")

                now_EBITMARGIN = _df[0]["EBITMARGIN"]
                last_EBITMARGIN = _df[1]["EBITMARGIN"]
                EBITG = ((now_EBITMARGIN - last_EBITMARGIN) / last_EBITMARGIN)

                df.iloc[number, 1] = EBITG
            except:
                df.iloc[number, 1] = -999

        # 求 归属母公司净利润增长率NPG
        _df = get_fundamentals(table='deriv_finance_indicator', symbols=symbol_list, start_date=day_time,
                               end_date=day_time,
                               fields="NPGRT", df=True)
        if len(_df) == len(symbol_list):
            df["NPG"] = _df["NPGRT"]
        else:
            for number in range(len(symbol_list)):
                try:
                    _df = get_fundamentals(table='deriv_finance_indicator', symbols=symbol_list[number],
                                           start_date=day_time,
                                           end_date=day_time, fields="NPGRT")
                    _NPG = qmtools.get_data_value(_df, "NPGRT")

                    df.iloc[number, 2] = _NPG[0]
                except:
                    df.iloc[number, 2] = -999
        # 求出 营业总收入增长率TAG
        _df = get_fundamentals(table='deriv_finance_indicator', symbols=symbol_list, start_date=day_time,
                               end_date=day_time,
                               fields="TAGRT", df=True)
        if len(_df) == len(symbol_list):
            df["TAG"] = _df["TAGRT"]
        else:
            for number in range(len(symbol_list)):
                try:
                    _df = get_fundamentals(table='deriv_finance_indicator', symbols=symbol_list[number],
                                           start_date=day_time,
                                           end_date=day_time, fields="TAGRT")
                    _TAG = qmtools.get_data_value(_df, "TAGRT")

                    df.iloc[number, 3] = _TAG[0]
                except:
                    df.iloc[number, 3] = -999

        # 求 营业毛利润GPG
        for number in range(len(symbol_list)):
            try:
                _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list[number],
                                         end_date=day_time,
                                         count=2, fields="OPGPMARGIN")

                now_GPG = _df[0]["OPGPMARGIN"]
                last_GPG = _df[1]["OPGPMARGIN"]
                GPG = ((now_GPG - last_GPG) / last_GPG)

                df.iloc[number, 4] = GPG
            except:
                df.iloc[number, 4] = -999

        # 求 营业利润率OPG
        for number in range(len(symbol_list)):
            try:
                _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list[number],
                                         end_date=day_time,
                                         count=2, fields="OPPRORT")

                now_OPG = _df[0]["OPPRORT"]
                last_OPG = _df[1]["OPPRORT"]
                OPG = ((now_OPG - last_OPG) / last_OPG)
                df.iloc[number, 5] = OPG
            except:
                df.iloc[number, 5] = -999
        # 求 每股现金流量净额OCG
        for number in range(len(symbol_list)):
            try:
                _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list[number],
                                         end_date=day_time,
                                         count=2, fields="NCFPS")
                now_EBITMARGIN = _df[0]["NCFPS"]
                last_EBITMARGIN = _df[1]["NCFPS"]
                EBITG = ((now_EBITMARGIN - last_EBITMARGIN) / last_EBITMARGIN)
                df.iloc[number, 6] = EBITG
            except:
                df.iloc[number, 6] = -999

        self.target_and_factor_list = df.dropna()
        return self.target_and_factor_list

    def sort_target_list(self, symbol_list: list | pd.DataFrame) -> list:
        if not isinstance(symbol_list, pd.DataFrame):
            return super().sort_target_list(symbol_list)
        df = symbol_list
        df_factor = df.iloc[:, 1:]
        df_factor = np.asarray(df_factor)

        # 先进行列归一化，然后在对每行进行标准化处理
        df_factor = preprocessing.MinMaxScaler().fit_transform(df_factor)
        weight = [[-1], [-1], [-1], [-1], [-1], [-1]]
        weight_mat = np.asmatrix(weight)
        res = np.dot(df_factor, weight_mat)
        df["score"] = (res)

        df = (df.sort_values(["score"]))
        # print(df)
        self.sorted_target_list.clear()
        for _ in df["symbol"].values:
            self.sorted_target_list.append(_)
        return self.sorted_target_list

    def try_to_order(self, symbol_list: list) -> Any:
        print(self.now, "order_close_all")
        order_close_all()
        print(self.now, "order_target_percent", symbol_list)
        for symbol in symbol_list:
            order_target_percent(symbol=symbol, percent=1. / self.top_count, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)

        # return super().order_op(symbol_list)


