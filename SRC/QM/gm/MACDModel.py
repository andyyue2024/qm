import time
from datetime import datetime, date
from typing import Any
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market
from QM import OrderOp
from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


class MACDModel(BaseGMModel):

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int = 5):
        super().__init__(index_list, now, top_count)

    def sell_target(self, target: str):
        super().sell_target(target)
        order_target_percent(symbol=target, percent=0, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def buy_target(self, target: str):
        super().buy_target(target)
        order_target_percent(symbol=target, percent=1./self.top_count, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def get_order_op(self, target: str) -> OrderOp:
        last_day = get_previous_trading_date("SHSE", self.now)
        # data = history_n(context.index, frequency="1d", count=30, end_time=last_day, fields="close", df=True)
        data = history_n(symbol=target, frequency="1d", count=35,
                         end_time=last_day, fields="close", fill_missing="last", adjust=ADJUST_PREV, df=True)
        close = data["close"].values
        macdDIFF, macdDEA, macd = qmtools.MACD_CN(close)
        if macd[-2] < 0 < macd[-1]:
            return OrderOp.BUY
        elif macd[-2] > 0 > macd[-1]:
            return OrderOp.SELL
        return super().get_order_op(target)

    def execute(self) -> Any:
        self.start_time = time.time()
        self.try_to_order(self.index_list)
        print(self.now, f"executing spend {time.time() - self.start_time} seconds")
