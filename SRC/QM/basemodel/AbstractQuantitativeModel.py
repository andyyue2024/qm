from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

from QM.basemodel.OrderOp import OrderOp


class AbstractQuantitativeModel(ABC):
    @abstractmethod
    def get_all_target_list(self, index_list: list) -> list:
        """
        获取指数列表所包含的全部标的
        :param index_list:
        :return: list
        """
        pass

    @abstractmethod
    def filter_target_list(self, target_list: list) -> list:
        """
        对标的列表依据财务指标进行过滤 或 根据黑名单进行过滤
        :param target_list:
        :return: list
        """
        pass

    @abstractmethod
    def get_target_and_factor_list(self, target_list: list) -> list | pd.DataFrame:
        """
        获取标及其因子列表。因子可以是实际值、相对值、差值
        :param target_list:
        :return: list | pd.DataFrame
        """
        pass

    @abstractmethod
    def sort_target_list(self, target_list: list | pd.DataFrame) -> list:
        """
        对因子结合权总进行综合排序
        :param target_list:
        :return: list
        """
        pass

    @abstractmethod
    def get_top_target_list(self, target_list: list, top_count: int) -> list:
        """
        获取取 TOP N的标的
        :param target_list:
        :param top_count:
        """
        pass

    @abstractmethod
    def try_to_order(self, target_list: list) -> Any:
        """
        调整 标的仓位
        :param target_list:
        """
        pass

    @abstractmethod
    def get_order_op(self, target: str) -> OrderOp:
        """
        获取单个标的 的操作方向
        :param target:
        """
        pass

    @abstractmethod
    def buy_target(self, target: str):
        """
        购买 单个标的
        :param target:
        """
        pass

    @abstractmethod
    def sell_target(self, target: str):
        """
        卖出 单个标的
        :param target:
        """
        pass

    @abstractmethod
    def execute(self) -> Any:
        """
        获取单个标的的操作方向
        """
        pass
