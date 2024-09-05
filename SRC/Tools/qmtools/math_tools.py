import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn import preprocessing


def get_data_value(data, factor):
    """
    获取返回的data数据中的对应因子的list
    :param data:
    :param factor:
    :return:
    """
    result = []
    for _ in data:
        result.append(_[factor])
    return result


def get_const_and_weight(X, Y):
    XX_ = sm.add_constant(X)
    model = sm.OLS(Y, XX_)
    results = model.fit()
    const, weight = results.params
    return const, weight


def get_delta_value_list(df, xlabels: list, ylabel):
    X = sm.add_constant(df[xlabels])
    model = sm.OLS(df[ylabel], X).fit()
    # model_summary = model.summary()
    # print(model_summary)
    df["predict_" + ylabel] = model.predict(X)
    df["d_value_" + ylabel] = df[ylabel] - df["predict_" + ylabel]  # 这里d_value是残差，大于0是高估，小于0是低估
    return df["d_value_" + ylabel].to_list()


def get_symbol_list_by_delta_value(df, xlabels: list, ylabel, ret_label):
    # 假设有一个数据集，包含三个自变量 (X1, X2, X3) 和一个因变量 (Y)
    # np.random.seed(0)
    # X1 = np.random.rand(100)
    # X2 = np.random.rand(100)
    # X3 = np.random.rand(100)
    # Y = 1.5 + 2*X1 + 3*X2 + 4*X3 + np.random.randn(100)
    # df = pd.DataFrame({'X1': X1, 'X2': X2, 'X3': X3, 'Y': Y})

    # 向自变量中添加一个常数项
    X = sm.add_constant(df[xlabels])
    model = sm.OLS(df[ylabel], X).fit()
    # model_summary = model.summary()
    # print(model_summary)
    # const = model.params[0:1]
    # weights = model.params[1:]
    # print(const, " ", weights)
    # print("model.params:", model.params)
    df["predict_" + ylabel] = model.predict(X)
    df["d_value"] = df[ylabel] - df["predict_" + ylabel]  # 这里d_value是残差，大于0是高估，小于0是低估
    df = df.sort_values(["d_value"])
    symbol_list = []
    symbol_list.extend(df[ret_label].values)
    return symbol_list


def get_symbol_list_by_weight_score(df, weight, start, end=0):
    """
        归一化是在列的方向对行数据进行操作：比如调用sklearn.preprocessing里的MinMaxscaler；
        标准化是在行的方向对列数据进行操作：比如调用sklearn.preprocessing里的Normalizer；
        因为是对 每行 求和，这里建议对建立的矩阵使用MinMaxscaler

    """
    if end == 0:
        df_factor = df.iloc[:, start:]
    else:
        df_factor = df.iloc[:, start:end]
    df_factor = np.asarray(df_factor)
    # 先进行列归一化，然后在对每行进行标准化处理
    df_factor = preprocessing.MinMaxScaler().fit_transform(df_factor)
    df_factor = preprocessing.Normalizer().fit_transform(df_factor)
    _weight = list(weight)
    weight_mat = np.asarray(_weight)
    res = np.dot(df_factor, weight_mat)
    df["score"] = res
    # df.index = df.score
    # df = df.sort_index(ascending=True)  # 这里是将最后的趋势有小到大排列
    df = (df.sort_values(["score"]))
    symbol_list = []
    symbol_list.extend(df["symbol"].values)
    return symbol_list


def get_max_corr_list(df: pd.DataFrame, num=10):
    """
    获取数据集的相关性系数
    :param df:
    :param num:
    :return:
    """
    corr = df.corr()
    # 找出相关性最大的股票标的
    corr_matrix = corr.as_matrix()  # 转化为矩阵
    corr_matrix[corr_matrix == 1] = 0  # 将1转为0

    raw, column = corr_matrix.shape  # get the matrix of a raw and column
    double_symbols_list = []
    for n in range(num):
        _position = np.argmax(corr_matrix)  # get the index of max in the a
        m, n = divmod(_position, column)

        corr_matrix[m, n] = corr_matrix[n, m] = 0
        double_symbols_list.append([corr.index[m], corr.index[n]])

    return double_symbols_list


def delta_edge(real, std_num=3):
    """
    首先是去极值的处理，去极值的本质就是使用均值的几倍标准差上下限去取代超过阈值的那个值
    edge_up = r.mean()+std*r.std()
    edge_low = r.mean()-std*r.std()
    r[r>edge_up] = edge_up
    r[r<edge_low] = edge_low

    去极值的处理说明
    来源：https://www.joinquant.com/post/12445?tag=algorithm
    """
    edge_up = real.mean() + std_num * real.std()
    edge_low = real.mean() - std_num * real.std()

    real[real > edge_up] = edge_up
    real[real < edge_low] = edge_low

    return real


def fast_delta_edge(real, std_num=3):
    _real = real
    real = []
    for _ in _real:
        real.append(_)

    edge_up = np.mean(real) + std_num * np.std(real)
    edge_low = np.mean(real) - std_num * np.std(real)

    result = []
    for _ in real:

        if _ > edge_up:
            result.append(edge_up)
        elif _ < edge_low:
            result.append(edge_low)
        else:
            result.append(_)
    return result
