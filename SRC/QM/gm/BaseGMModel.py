import time
from datetime import datetime, date
from typing import Any

import pandas as pd
from QM.basemodel import *
from Tools import qmtools


class BaseGMModel(BaseQuantitativeModel):

    def __init__(self, index_list: list, now: str | datetime | date, top_count: int):
        super().__init__(index_list, now, top_count)
        self.start_time = 0

    def get_all_target_list(self, index_list: list) -> list:
        self.all_target_list.clear()
        for index in index_list:
            _symbol_list = qmtools.get_symbol_list(index, self.now)
            self.all_target_list.extend(_symbol_list)
        return self.all_target_list

    def sort_target_list(self, symbol_list: list | pd.DataFrame) -> list:
        self.sorted_target_list.clear()
        if isinstance(symbol_list, pd.DataFrame):
            self.sorted_target_list.extend(symbol_list["symbol"].values)
        elif isinstance(symbol_list, list):
            self.sorted_target_list.extend(symbol_list)
        return self.sorted_target_list

    def sell_target(self, target: str):
        print(self.now, "order_sell_target: ", target)

    def buy_target(self, target: str):
        print(self.now, "order_buy_target: ", target)

    def execute(self) -> Any:
        self.start_time = time.time()
        super().execute()
        print(self.now, f"executing spend {time.time() - self.start_time} seconds")

