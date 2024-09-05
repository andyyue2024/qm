import time
from datetime import datetime, date
from typing import Any
import numpy as np
import pandas as pd
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market
from sklearn import preprocessing
from QM import OrderOp
from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


# 改进的RSRS因子 回测
class RSRSModel(BaseGMModel):

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int = 5):
        super().__init__(index_list, now, top_count)

    def sell_target(self, target: str):
        super().sell_target(target)
        order_target_percent(symbol=target, percent=0, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def buy_target(self, target: str):
        super().buy_target(target)
        order_target_percent(symbol=target, percent=1, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def get_order_op(self, target: str) -> OrderOp:
        last_day = get_previous_trading_date("SHSE", self.now)
        rsrs_weight = qmtools.get_rsrs_weight(target, last_day)
        if rsrs_weight > 0.7:
            return OrderOp.BUY
        elif rsrs_weight < -0.7:
            return OrderOp.SELL
        return super().get_order_op(target)

    def execute(self) -> Any:
        self.start_time = time.time()
        self.try_to_order(self.index_list)
        print(self.now, f"executing spend {time.time() - self.start_time} seconds")
