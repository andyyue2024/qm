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


# 一个适合中长线的 回测
# Volume Increase and Price Amplitude Model
# 找到昨天之前成交量大于昨天的成交量（0.8倍），这个区间的天数大于30天
# 昨天单日成交量大于该区间的平均成交量的2倍
# 区间价格波动小于10%
# Volume Increase and Price Amplitude Model
class VIPAModel(BaseGMModel):

    def __init__(self, index_list: list, now: str | datetime | date, positions: list):
        super().__init__(index_list, now, 5)
        self.hold_target_list = qmtools.get_data_value(positions, "symbol")

    def filter_target_list(self, symbol_list: list) -> list:
        self.filtered_target_list.clear()
        for symbol in symbol_list:
            if symbol not in self.black_target_list:
                self.filtered_target_list.append(symbol)
        return self.filtered_target_list

    def try_to_order_for_holdings(self, symbol_list: list) -> Any:
        """
        检查是否卖出持仓
        :param symbol_list:
        :return:
        """
        for target in self.hold_target_list:
            if qmtools.sell_check(self.now, target):
                self.sell_target(target)
                self.black_target_list.append(target)

    def try_to_order(self, target_list: list) -> Any:
        for target in target_list:
            if qmtools.buy_check(self.now, target):
                self.buy_target(target)

    def sell_target(self, target: str):
        super().sell_target(target)
        order_target_percent(symbol=target, percent=0, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def buy_target(self, target: str):
        super().buy_target(target)
        order_target_percent(symbol=target, percent=1. / self.top_count, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def execute(self) -> Any:
        self.start_time = time.time()
        self.try_to_order_for_holdings(self.hold_target_list)
        if len(self.index_list) <= 0:
            return
        self.get_all_target_list(self.index_list)

        if len(self.all_target_list) <= 0:
            return
        self.filter_target_list(self.all_target_list)

        if len(self.filtered_target_list) <= 0:
            return
        self.get_top_target_list(self.filtered_target_list, self.top_count)

        if len(self.top_target_list) <= 0:
            return
        self.try_to_order(self.top_target_list)
        print(self.now, f"executing spend {time.time() - self.start_time} seconds")
        return self
