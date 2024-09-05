from datetime import datetime, date
from typing import Any
import numpy as np
import pandas as pd
# Goldminer3-x64-3.20.2.5
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market
from sklearn import preprocessing
from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


class HowardRothmanModel(BaseGMModel):

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int = 5):
        super().__init__(index_list, now, top_count)

    def filter_target_list(self, symbol_list: list) -> list:
        # fields: str | list = None, filters: str = None
        self.filtered_target_list.clear()
        # bank_list = qmtools.get_symbol_list("SHSE.000947", now)
        # stock_company_list = qmtools.get_symbol_list("SZSE.399975", now)
        #
        # for _ in _symbol_list:
        #     # if (_ not in bank_list) and (_ not in stock_company_list):
        #     symbol_list.append(_)
        # if len(symbol_list) <= 0:
        #     return symbol_list

        # 1  总市值≧市场平均值*1.0：
        # 2  最近一季流动比率≧市场平均值。
        # TOTMKTCAP	总市值
        # PCTTM	市现率TTM
        df = get_fundamentals_n(table='trading_derivative_indicator', symbols=symbol_list, end_date=self.now,
                                fields="TOTMKTCAP,PCTTM", df=True)
        TOTMKTCAP_mean = df["TOTMKTCAP"].mean()
        PCTTM_mean = df["PCTTM"].mean()
        df = df[df["TOTMKTCAP"] > TOTMKTCAP_mean]
        df = df[df["PCTTM"] > PCTTM_mean]

        # print(df)
        self.filtered_target_list.clear()
        self.filtered_target_list.extend(df["symbol"].values)
        if len(self.filtered_target_list) <= 0:
            return self.filtered_target_list

        # 5.近四季营收成长率介于6%至30%。             由高到低 NPGRT
        # 6.近四季盈余成长率介于8%至50%。      净利润       由高到低 TAGRT
        # NPGRT	归属母公司净利润增长率
        # TAGRT	营业总收入增长率
        # ROEAVGCUT	净资产收益率_平均(扣除非经常损益)
        # FCFEPS 每股股东自由现金流量
        df = get_fundamentals_n(table='deriv_finance_indicator', symbols=self.filtered_target_list, end_date=self.now,
                                fields="NPGRT, TAGRT", filter="NPGRT > 6 and NPGRT < 30 and TAGRT > 8 and TAGRT < 50",
                                df=True)
        # print(df)
        self.filtered_target_list.clear()
        self.filtered_target_list.extend(df["symbol"].values)
        return self.filtered_target_list

    def get_target_and_factor_list(self, symbol_list: list) -> list | pd.DataFrame:
        # fields: str | list = None, filters: str = None
        df = pd.DataFrame([])
        df["symbol"] = symbol_list
        df["ROEAVGCUT"] = -999
        df["FCFEPS"] = -999
        _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list, end_date=self.now,
                                 fields="ROEAVGCUT, FCFEPS", df=True)

        if len(_df) == len(symbol_list):
            df["ROEAVGCUT"] = _df["ROEAVGCUT"]
            df["FCFEPS"] = _df["FCFEPS"]
        else:
            for number in range(len(symbol_list)):
                try:
                    _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol_list[number],
                                             end_date=self.now, fields="ROEAVGCUT,FCFEPS")
                    _factor_value = qmtools.get_data_value(_df, "ROEAVGCUT")
                    df.iloc[number, 1] = _factor_value[0]

                    _factor_value = qmtools.get_data_value(_df, "FCFEPS")
                    df.iloc[number, 2] = _factor_value[0]
                except:
                    df.iloc[number, 1] = np.mean(df["ROEAVGCUT"])
                    df.iloc[number, 2] = np.mean(df["FCFEPS"])

        self.target_and_factor_list = df.dropna()
        return self.target_and_factor_list

    def sort_target_list(self, symbol_list: list | pd.DataFrame) -> list:
        if not isinstance(symbol_list, pd.DataFrame):
            return super().sort_target_list(symbol_list)
        df = symbol_list
        df_factor = df.iloc[:, 1:]
        # df_factor = df.iloc[:, 5:]
        df_factor = np.asarray(df_factor)

        # 先进行列归一化，然后在对每行进行标准化处理
        df_factor = preprocessing.MinMaxScaler().fit_transform(df_factor)

        weight = [[-1], [-1]]
        weight_mat = np.asmatrix(weight)
        res = np.dot(df_factor, weight_mat)
        df["score"] = res

        df = (df.sort_values(["score"]))
        self.sorted_target_list.clear()
        self.sorted_target_list.extend(df["symbol"].values)
        return self.sorted_target_list

    def try_to_order(self, symbol_list: list) -> Any:
        print(self.now, "order_close_all")
        order_close_all()
        print(self.now, "order_target_percent", symbol_list)
        for symbol in symbol_list:
            order_target_percent(symbol=symbol, percent=1. / self.top_count, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)

        # return super().order_op(symbol_list)
