from datetime import datetime, date
from typing import Any
import pandas as pd

from QM.basemodel.AbstractQuantitativeModel import AbstractQuantitativeModel
from QM.basemodel.OrderOp import OrderOp


class BaseQuantitativeModel(AbstractQuantitativeModel):
    black_target_list = []

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int):
        super().__init__()
        self.index_list = list(index_list)
        self.now = now
        self.top_count = top_count
        self.all_target_list = []
        self.filtered_target_list = []
        self.target_and_factor_list = None
        self.sorted_target_list = []
        self.top_target_list = []

    def get_all_target_list(self, index_list: list) -> list:
        return self.all_target_list

    def filter_target_list(self, target_list: list) -> list:
        self.filtered_target_list.clear()
        self.filtered_target_list.extend(target_list)  # default not filter any item
        return self.filtered_target_list

    def get_target_and_factor_list(self, target_list: list) -> list | pd.DataFrame:
        return self.target_and_factor_list

    def sort_target_list(self, target_list: list | pd.DataFrame) -> list:
        return self.sorted_target_list

    def get_top_target_list(self, target_list: list, top_count: int) -> list:
        self.top_target_list.clear()
        self.top_target_list.extend(target_list[:top_count])
        return self.top_target_list

    def try_to_order(self, target_list: list) -> Any:
        for target in target_list:
            oo = self.get_order_op(target)
            if OrderOp.BUY == oo:
                self.buy_target(target)
            elif OrderOp.SELL == oo:
                self.sell_target(target)
            elif OrderOp.NOTHING == oo:
                pass

    def get_order_op(self, target: str) -> OrderOp:
        return OrderOp.NOTHING

    def buy_target(self, target: str):
        pass

    def sell_target(self, target: str):
        pass

    def execute(self) -> Any:
        if len(self.index_list) <= 0:
            return
        self.get_all_target_list(self.index_list)

        if len(self.all_target_list) <= 0:
            return
        self.filter_target_list(self.all_target_list)

        if len(self.filtered_target_list) <= 0:
            return
        self.get_target_and_factor_list(self.filtered_target_list)

        if len(self.target_and_factor_list) <= 0:
            return
        self.sort_target_list(self.target_and_factor_list)

        if len(self.sorted_target_list) <= 0:
            return
        self.get_top_target_list(self.sorted_target_list, self.top_count)

        if len(self.top_target_list) <= 0:
            return
        self.try_to_order(self.top_target_list)
        return self

    @staticmethod
    def reset():
        BaseQuantitativeModel.black_target_list.clear()

    @staticmethod
    def train():
        print("training...")
