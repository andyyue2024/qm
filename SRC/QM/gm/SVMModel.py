import time
from datetime import datetime, date
from typing import Any
import numpy as np
from gm.api import *
from gm.enum import PositionSide_Long, OrderType_Market
from sklearn import svm
from QM import OrderOp
from QM.gm.BaseGMModel import BaseGMModel
from Tools import qmtools


# 使用支持向量机进行回测
# Support Vector Classification
class SVMModel(BaseGMModel):
    svc = None
    price = 0.0
    def __init__(self, index_list: list, now: str | datetime | date, position: Any):
        super().__init__(index_list, now, 5)
        self.position = position

    def sell_target(self, target: str):
        # super().sell_target(target)
        order_close_all()

    def buy_target(self, target: str):
        # super().buy_target(target)
        # 把标的的仓位调至95%
        print(f'     {target}以市价单开多仓到仓位0.95')
        order_target_percent(symbol=target, percent=0.95, order_type=OrderType_Market,
                             position_side=PositionSide_Long)

    def get_order_op(self, target: str) -> OrderOp:
        recent_data = history_n(target, frequency='1d', end_time=self.now, count=1,
                                fields="open,close,high,low,volume", fill_missing='last', df=True)

        bar_close = recent_data['close'].values[0]

        # 获取数据并计算相应的因子
        # 于星期一的09:31:00进行操作
        # 当前bar的工作日
        weekday = self.now.isoweekday()
        # 获取模型相关的数据
        # 获取持仓
        # 如果日期是新的星期一且没有仓位则开始预测
        if not self.position and weekday == 1:
            # 获取预测用的历史数据
            data = history_n(symbol=target, frequency='1d', end_time=self.now, count=15,
                             fill_missing='last', df=True)
            close = data['close'].values
            train_max_x = data['high'].values
            train_min_n = data['low'].values
            train_amount = data['amount'].values
            volume = []
            for i in range(len(close)):
                volume_temp = train_amount[i] / close[i]
                volume.append(volume_temp)
            close_mean = close[-1] / np.mean(close)
            volume_mean = volume[-1] / np.mean(volume)
            max_mean = train_max_x[-1] / np.mean(train_max_x)
            min_mean = train_min_n[-1] / np.mean(train_min_n)
            vol = volume[-1]
            return_now = close[-1] / close[0]
            std = np.std(np.array(close), axis=0)
            # 得到本次输入模型的因子
            features = [close_mean, volume_mean, max_mean, min_mean, vol, return_now, std]
            features = np.array(features).reshape(1, -1)
            prediction = SVMModel.svc.predict(features)[0]
            # 若预测值为上涨则开仓
            if prediction == 1:
                # 获取昨收盘价
                SVMModel.price = close[-1]
                return OrderOp.BUY

        # 当涨幅大于10%,平掉所有仓位止盈
        elif self.position and bar_close / SVMModel.price >= 1.10:
            print(f'      {target}以市价单全平多仓止盈')
            return OrderOp.SELL

        # 当时间为周五并且跌幅大于2%时,平掉所有仓位止损
        elif self.position and bar_close / SVMModel.price < 1.02 and weekday == 5:
            print(f'      {target}以市价单全平多仓止损')
            return OrderOp.SELL
        return super().get_order_op(target)

    def execute(self) -> Any:
        self.start_time = time.time()
        self.try_to_order(self.index_list)
        print(self.now, f"executing spend {time.time() - self.start_time} seconds")

    @staticmethod
    def train(symbol, start_date, end_date):
        """
        使用SVM对 标的 的历史数据进行训练
        :param symbol: 标的
        :param start_date: SVM训练起始时间
        :param end_date: SVM训练终止时间
        :return:
        """
        start_time = time.time()
        # 用于记录工作日
        # 获取目标股票的daily历史行情
        recent_data = history(symbol, frequency='1d', start_time=start_date, end_time=end_date,
                              fill_missing='last', df=True)
        days_value = recent_data['bob'].values
        days_close = recent_data['close'].values
        days = []
        # 获取行情日期列表
        print('准备数据训练SVM')
        for i in range(len(days_value)):
            days.append(str(days_value[i])[0:10])
        x_all = []
        y_all = []
        for index in range(15, (len(days) - 5)):
            # 计算三星期共15个交易日相关数据
            # start_day = days[index - 15]
            # end_day = days[index]
            # data = history(context.symbol, frequency='1d', start_time=start_day, end_time=end_day,
            # fill_missing='last', df=True)
            data = recent_data.iloc[index - 15: index, :]
            close = data['close'].values
            max_x = data['high'].values
            min_n = data['low'].values
            amount = data['amount'].values
            volume = []
            for i in range(len(close)):
                volume_temp = amount[i] / close[i]
                volume.append(volume_temp)
            close_mean = close[-1] / np.mean(close)  # 收盘价/均值
            volume_mean = volume[-1] / np.mean(volume)  # 现量/均量
            max_mean = max_x[-1] / np.mean(max_x)  # 最高价/均价
            min_mean = min_n[-1] / np.mean(min_n)  # 最低价/均价
            vol = volume[-1]  # 现量
            return_now = close[-1] / close[0]  # 区间收益率
            std = np.std(np.array(close), axis=0)  # 区间标准差
            # 将计算出的指标添加到训练集X
            # features用于存放因子
            features = [close_mean, volume_mean, max_mean, min_mean, vol, return_now, std]
            x_all.append(features)
        # 准备算法需要用到的数据
        for i in range(len(days_close) - 20):
            if days_close[i + 20] > days_close[i + 15]:
                label = 1
            else:
                label = 0
            y_all.append(label)
        x_train = x_all[: -1]
        y_train = y_all[: -1]
        # 训练SVM
        SVMModel.svc = svm.SVC(C=1.0, kernel='rbf', degree=3, gamma='auto', coef0=0.0, shrinking=True,
                               probability=False,
                               tol=0.001, cache_size=200, verbose=False, max_iter=-1,
                               decision_function_shape='ovr', random_state=None)
        SVMModel.svc.fit(x_train, y_train)
        print(f"训练完成!, time elapsed: {time.time() - start_time} seconds")
