from datetime import datetime, date
from typing import Any

import pandas as pd
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market

from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


class DefensiveStrategyModel(BaseGMModel):
    """
    防守型策略
    中证红利策略
    """
    def __init__(self, index_list: list, now: str | datetime | date, top_count: int = 5):
        super().__init__(index_list, now, top_count)

    def get_target_and_factor_list(self, symbol_list: list) -> list | pd.DataFrame:
        """
         排名条件设市盈率从小到大，权重2；  PETTM
         股息率从大到小，权重1； DY
         市净率从小到大，权重3； PB
         历史贝塔从小到大，权重2； 代表与大盘的联动波动率
         自定义波动率指标从小到大权重10，
         """
        F_PETTM = "PETTM"
        F_DY = "DY"
        F_PB = "PB"
        tables = qmtools.get_table_names_by_factors([F_PETTM, F_DY, F_PB])

        PETTM = qmtools.fast_batch_get_neutralized_factor(symbol_list, tables[F_PETTM], F_PETTM, self.now, more_is_better=False)
        DY = qmtools.fast_batch_get_neutralized_factor(symbol_list, tables[F_DY], F_DY, self.now, more_is_better=True)
        PB = qmtools.fast_batch_get_neutralized_factor(symbol_list, tables[F_PB], F_PB, self.now, more_is_better=False)

        beta = {}
        volatility = {}
        for symbol in symbol_list:
            beta[symbol] = qmtools.get_beta_weight_2(symbol, self.now, count=30)
            volatility[symbol] = qmtools.get_volatility_normal(symbol, self.now, count=30)

        df = pd.DataFrame([])
        df["symbol"] = PETTM.keys()
        df["PETTM"] = PETTM.values()
        df["PB"] = PB.values()
        df["DY"] = DY.values()
        df["beta"] = beta.values()
        df["volatility"] = volatility.values()

        self.target_and_factor_list = df.dropna()
        return self.target_and_factor_list

    def sort_target_list(self, df: list | pd.DataFrame) -> list:
        if not isinstance(df, pd.DataFrame):
            return super().sort_target_list(df)
        self.sorted_target_list.clear()
        weight = [1, -1, -1, -1, -1]
        symbol_list = qmtools.get_symbol_list_by_weight_score(df, weight, start=1)
        self.sorted_target_list.extend(symbol_list)
        return self.sorted_target_list

    def try_to_order(self, symbol_list: list) -> Any:
        print(self.now, "order_close_all")
        order_close_all()
        print(self.now, "order_target_percent", symbol_list)
        for symbol in symbol_list:
            order_target_percent(symbol=symbol, percent=1. / self.top_count, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)

        # return super().order_op(symbol_list)


