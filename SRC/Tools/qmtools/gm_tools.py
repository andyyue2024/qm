import csv
from datetime import *

from gm.api import *

from Tools.qmtools.gm_table_tools import *
from Tools.qmtools.show_tools import *


# 这里是获取指数列表中的全部标的列表
# 内部将按照指定日期的上一个交易日去获取列表
def get_symbol_list_from_indexes(index_list, now):
    if index_list is None:
        return []
    # last_day = get_previous_trading_date("SHSE", now)
    # last_day_SZ = get_previous_trading_date("SZSE", now)
    target_set = set()
    for index in index_list:
        # if index.startswith("SZSE"):
        #     last_day = last_day_SZ
        _symbol_list = get_symbol_list(index, now)
        target_set.update(_symbol_list)
    return list(target_set)


# 获取指定日期下的指数对应的有效成分股
def get_symbol_list(index, now):
    # type: (str, str|datetime|date) -> list
    """
    获取指数对应的有效成分股
    :param index:
    :param now:
    :return:
    """
    ret_list = []
    try:
        symbol_list = get_history_constituents(index=index, start_date=now)[0].get("constituents").keys()
        symbol_list_not_suspended = get_history_instruments(symbols=symbol_list, start_date=now, end_date=now)
        symbol_list = [item['symbol'] for item in symbol_list_not_suspended if not item['is_suspended']]
    except:
        return ret_list
    ret_list.extend(symbol_list)
    return ret_list


# 过滤某些行业的标的
def filter_black_list(origin_symbol_list, now, black_index_list: list = None):
    symbol_list = list(origin_symbol_list)
    if black_index_list is None:  # when not needed filter
        return symbol_list
    # last_day = last_day_SH = get_previous_trading_date("SHSE", now)
    # last_day_SZ = get_previous_trading_date("SZSE", now)
    for index in black_index_list:
        # if index.startswith("SHSE"):
        #     last_day = last_day_SH
        # elif index.startswith("SZSE"):
        #     last_day = last_day_SZ
        black_list = get_symbol_list(index, now)
        symbol_list = [item for item in symbol_list if item not in black_list]
    return symbol_list


def get_history_instruments_without_limit(symbols, start_date, end_date, fields=None, df=False, api_limit_count=200):
    # type: (str|list, str|datetime|date, str|datetime|date, str|list, bool, int) -> list[dict]|pd.DataFrame
    """
        返回指定的symbols的标的日指标数据
        并规避get_history_instruments的参数symbols的200限制。
    """

    API_LIMIT_COUNT = api_limit_count
    num = (len(symbols) + API_LIMIT_COUNT - 1) // API_LIMIT_COUNT
    remainder = len(symbols) % API_LIMIT_COUNT
    ret_df = pd.DataFrame([])
    ret_list = []
    for i in range(num):
        start = i * API_LIMIT_COUNT
        end = (i + 1) * API_LIMIT_COUNT
        if end > len(symbols):
            end = start + remainder
        ret_tmp = get_history_instruments(symbols=symbols[start: end], start_date=start_date, end_date=end_date,
                                          fields=fields, df=df)
        if df:
            ret_df = pd.concat([ret_df, ret_tmp], ignore_index=True)
        else:
            ret_list.extend(ret_tmp)
    if df:
        return ret_df
    else:
        return ret_list


def get_fundamentals_without_limit(table, symbols, start_date, end_date, fields=None, filter=None,
                                   order_by=None, limit=1000, df=False, api_limit_count=200):
    # type: (str, str|list, str|datetime|date, str|datetime|date, str|list, str, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
        查询基本面财务数据
        并规避get_fundamentals的参数symbols的200限制。
    """

    API_LIMIT_COUNT = api_limit_count
    num = (len(symbols) + API_LIMIT_COUNT - 1) // API_LIMIT_COUNT
    remainder = len(symbols) % API_LIMIT_COUNT
    ret_df = pd.DataFrame([])
    ret_list = []
    for i in range(num):
        start = i * API_LIMIT_COUNT
        end = (i + 1) * API_LIMIT_COUNT
        if end > len(symbols):
            end = start + remainder
        ret_tmp = get_fundamentals(table=table, symbols=symbols[start: end], start_date=start_date, end_date=end_date,
                                   fields=fields, filter=filter, order_by=order_by, limit=limit, df=df)
        if df:
            ret_df = pd.concat([ret_df, ret_tmp], ignore_index=True)
        else:
            ret_list.extend(ret_tmp)
    if df:
        return ret_df
    else:
        return ret_list


def get_fundamentals_without_limit2(symbols, start_date, end_date, fields_and_filter,
                                    order_by=None, limit=1000, df=False, api_limit_count=200):
    # type: (str|list, str|datetime|date, str|datetime|date, dict, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
        查询基本面财务数据
        根据字段和条件自动查表合并数据(merge df, and then concat df)
        并规避get_fundamentals的参数symbols的200限制。
    """
    # Step1: create table and factor dict
    table_and_factor_dict = get_table_and_factor_dict(fields_and_filter)
    API_LIMIT_COUNT = api_limit_count
    num = (len(symbols) + API_LIMIT_COUNT - 1) // API_LIMIT_COUNT
    remainder = len(symbols) % API_LIMIT_COUNT
    ret_df = pd.DataFrame([])
    # ret_df["symbol"] = symbols
    # ret_list = []
    for i in range(num):
        start = i * API_LIMIT_COUNT
        end = (i + 1) * API_LIMIT_COUNT
        if end > len(symbols):
            end = start + remainder
        ret_tmp = pd.DataFrame([])
        ret_tmp["symbol"] = symbols[start: end]
        # Step2: call get_fundamentals() with different tables .
        for table, inner_dict in table_and_factor_dict.items():
            fields_str, filters_str = get_fields_and_filters(inner_dict)
            ret_tmp_part = get_fundamentals(table=table, symbols=symbols[start: end], start_date=start_date,
                                            end_date=end_date,
                                            fields=fields_str, filter=filters_str, order_by=order_by, limit=limit,
                                            df=True)
            field_keys = ['symbol']
            field_keys.extend(inner_dict.keys())
            ret_tmp_part = ret_tmp_part[field_keys]
            # Step3: merge df
            ret_tmp = pd.merge(ret_tmp, ret_tmp_part, on='symbol', how='inner')

        # And then, concat df
        ret_df = pd.concat([ret_df, ret_tmp], ignore_index=True)

    if df:
        return ret_df
    else:
        return ret_df.to_dict(orient='records')


def get_fundamentals_without_limit3(symbols, start_date, end_date, fields_and_filter,
                                    order_by=None, limit=1000, df=False, api_limit_count=200):
    # type: (str|list, str|datetime|date, str|datetime|date, dict, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
        查询基本面财务数据
        根据字段和条件自动查表合并数据(concat df, and then merge df)
        并规避get_fundamentals的参数symbols的200限制。
    """
    # Step1: create table and factor dict
    table_and_factor_dict = get_table_and_factor_dict(fields_and_filter)
    ret_df = pd.DataFrame([])
    ret_df["symbol"] = symbols
    # Step2: call get_fundamentals() with different tables .
    for table, inner_dict in table_and_factor_dict.items():
        fields_str, filters_str = get_fields_and_filters(inner_dict)
        # And then, concat df by call get_fundamentals_without_limit
        ret_tmp_part = get_fundamentals_without_limit(table=table, symbols=symbols, start_date=start_date,
                                                      end_date=end_date, fields=fields_str, filter=filters_str,
                                                      order_by=order_by, limit=limit, df=True,
                                                      api_limit_count=api_limit_count)
        field_keys = ['symbol']
        field_keys.extend(inner_dict.keys())
        ret_tmp_part = ret_tmp_part[field_keys]
        # Step3: merge df
        ret_df = pd.merge(ret_df, ret_tmp_part, on='symbol', how='inner')
    if df:
        return ret_df
    else:
        return ret_df.to_dict(orient='records')


def get_fundamentals_n_without_limit(table, symbols, end_date, fields=None, filter=None,
                                     order_by=None, count=1, df=False, api_limit_count=200):
    # type: (str, str|list, str|datetime|date, str|list, str, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
        查询基本面财务数据
        并规避get_fundamentals的参数symbols的200限制。
    """

    API_LIMIT_COUNT = api_limit_count
    num = (len(symbols) + API_LIMIT_COUNT - 1) // API_LIMIT_COUNT
    remainder = len(symbols) % API_LIMIT_COUNT
    ret_df = pd.DataFrame([])
    ret_list = []
    for i in range(num):
        start = i * API_LIMIT_COUNT
        end = (i + 1) * API_LIMIT_COUNT
        if end > len(symbols):
            end = start + remainder
        ret_tmp = get_fundamentals_n(table=table, symbols=symbols[start: end], end_date=end_date,
                                     fields=fields, filter=filter, order_by=order_by, count=count, df=df)
        if df:
            ret_df = pd.concat([ret_df, ret_tmp], ignore_index=True)
        else:
            ret_list.extend(ret_tmp)
    if df:
        return ret_df
    else:
        return ret_list


def get_fundamentals_n_without_limit2(symbols, end_date, fields_and_filter,
                                      order_by=None, count=1, df=False, api_limit_count=200):
    # type: (str|list, str|datetime|date, dict, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
            查询基本面财务数据
            根据字段和条件自动查表合并数据(merge df, and then concat df)
            并规避get_fundamentals的参数symbols的200限制。
        """
    # Step1: create table and factor dict
    table_and_factor_dict = get_table_and_factor_dict(fields_and_filter)
    API_LIMIT_COUNT = api_limit_count
    num = (len(symbols) + API_LIMIT_COUNT - 1) // API_LIMIT_COUNT
    remainder = len(symbols) % API_LIMIT_COUNT
    ret_df = pd.DataFrame([])
    # ret_df["symbol"] = symbols
    # ret_list = []
    for i in range(num):
        start = i * API_LIMIT_COUNT
        end = (i + 1) * API_LIMIT_COUNT
        if end > len(symbols):
            end = start + remainder
        ret_tmp = pd.DataFrame([])
        ret_tmp["symbol"] = symbols[start: end]
        # Step2: call get_fundamentals() with different tables .
        for table, inner_dict in table_and_factor_dict.items():
            fields_str, filters_str = get_fields_and_filters(inner_dict)
            ret_tmp_part = get_fundamentals_n(table=table, symbols=symbols, end_date=end_date,
                                              fields=fields_str, filter=filters_str,
                                              order_by=order_by, count=count, df=True)
            field_keys = ['symbol']
            field_keys.extend(inner_dict.keys())
            ret_tmp_part = ret_tmp_part[field_keys]
            # Step3: merge df
            ret_tmp = pd.merge(ret_tmp, ret_tmp_part, on='symbol', how='inner')

        # And then, concat df
        ret_df = pd.concat([ret_df, ret_tmp], ignore_index=True)

    if df:
        return ret_df
    else:
        return ret_df.to_dict(orient='records')


def get_fundamentals_n_without_limit3(symbols, end_date, fields_and_filter,
                                      order_by=None, count=1, df=False, api_limit_count=200):
    # type: (str|list, str|datetime|date, dict, str, int, bool, int) -> list[dict]|pd.DataFrame
    """
        查询基本面财务数据(concat df, and then merge df)
        并规避get_fundamentals的参数symbols的200限制。
    """
    # Step1: create table and factor dict
    table_and_factor_dict = get_table_and_factor_dict(fields_and_filter)
    ret_df = pd.DataFrame([])
    ret_df["symbol"] = symbols
    # Step2: call get_fundamentals() with different tables .
    for table, inner_dict in table_and_factor_dict.items():
        fields_str, filters_str = get_fields_and_filters(inner_dict)
        # And then, concat df by call get_fundamentals_n_without_limit
        ret_tmp_part = get_fundamentals_n_without_limit(table=table, symbols=symbols, end_date=end_date,
                                                        fields=fields_str, filter=filters_str,
                                                        order_by=order_by, count=count, df=True,
                                                        api_limit_count=api_limit_count)
        field_keys = ['symbol']
        field_keys.extend(inner_dict.keys())
        ret_tmp_part = ret_tmp_part[field_keys]
        # Step3: merge df
        ret_df = pd.merge(ret_df, ret_tmp_part, on='symbol', how='inner')
    if df:
        return ret_df
    else:
        return ret_df.to_dict(orient='records')


def get_roe_roic_list(symbol_list, last_day, count=14, std=0.11):
    """
    # 获取ROE/ROIC 的std < 给定值的标的列表
    # 其中，ROE 净资产收益率_平均(扣除非经常损益)；ROIC 投入资本回报率
    :param symbol_list:
    :param last_day:
    :param count:
    :param std:
    :return:
    """
    # 第一步：获取ROE/ROIC的std
    symbol_ROE_ROIC_list = []
    for symbol in symbol_list:
        try:
            _df = get_fundamentals_n(table='deriv_finance_indicator', symbols=symbol, count=count, end_date=last_day,
                                     fields="ROEAVGCUT,ROIC", df=True)
            if len(_df) < count - 2:
                pass
            else:
                _df = _df.dropna()
                _df["盈利性"] = _df["ROEAVGCUT"] / _df["ROIC"]
                dta_std = np.std(_df["盈利性"].values.tolist())
                if dta_std < std:
                    symbol_ROE_ROIC_list.append(symbol)
        except:
            pass
    # print(len(symbol_ROE_ROIC_list)) 155
    return symbol_ROE_ROIC_list


# ROE/ROIC 的std < 给定值
# ROE 净资产收益率_平均(扣除非经常损益)
# ROIC 投入资本回报率
# PETTM 市盈率TTM, 11 < PETTM  < 27
# NPGRT 归属母公司净利润增长率 10 < NPGRT < 39
# TAGRT 营业总收入增长率 10 < TAGRT < 39
def get_target_list_base(now, count=14, std=0.11):
    last_day = get_previous_trading_date("SHSE", now)
    index_list = {"SHSE.000010": "上证180", "SHSE.000016": "上证50", "SHSE.000300": "沪深300",
                  "SHSE 000903": "中证100", "SHSE.000904": "中证200", "SHSE.000905": "中证500",
                  "SHSE.000906": "中证800", "SHSE.000907": "中证700", "SHSE.000852": "中证1000"}
    # 这里是获取全A股的股票列表
    symbol_list = get_symbol_list_from_indexes(index_list, now)
    symbol_list = filter_black_list(symbol_list, now, ["SHSE.000947", "SZSE.399975", "SHSE.000948"])

    # 第一步：获取ROE/ROIC的std
    symbol_ROE_ROIC_list = get_roe_roic_list(symbol_list, last_day, count, std)

    # 第二步：这里假设PETTM在正常水平，即 11 < PETTM  < 27
    # 第三步：NPGRT  TAGRT
    factor_dict = {
        # "ROEAVGCUT": "",
        # "ROIC": "",
        "PETTM": "PETTM > 11 and PETTM < 27",
        "TAGRT": "TAGRT > 10 and TAGRT < 39",
        "NPGRT": "NPGRT > 10 and NPGRT < 39",
    }
    df = get_fundamentals_n_without_limit3(symbols=symbol_ROE_ROIC_list, end_date=last_day,
                                           fields_and_filter=factor_dict, df=True)

    # Step 4: query to filter
    # df = df[(df['PB'] > 0) & (df['ROE'] > 0)]
    # df = df.query('PB > 2 and ROE > 0')
    df = df.dropna()
    return list(df["symbol"].to_list())


def get_target_list_by_pb_roe(_symbol_list, now):
    last_day = get_previous_trading_date("SHSE", now)
    symbol_list = filter_black_list(_symbol_list, now, ["SHSE.000947", "SZSE.399975", "SHSE.000948"])

    _df = get_fundamentals_without_limit(table='deriv_finance_indicator', symbols=symbol_list, start_date=last_day,
                                         end_date=last_day,
                                         fields='TAGRT,NPGRT', filter="NPGRT > 21 and TAGRT > 20", df=True)
    _df = _df.dropna()
    symbol_list = []
    for _ in _df["symbol"].values:
        symbol_list.append(_)
    white_list = []
    symbol_list = symbol_list + white_list

    df = pd.DataFrame([])
    df["symbol"] = symbol_list

    # 求PB
    _df = get_fundamentals_without_limit(table='trading_derivative_indicator', symbols=symbol_list, start_date=last_day,
                                         end_date=last_day, fields="PB", filter="PB>0", df=True)
    print("got pb data")  # spend 120s
    _df = _df[['symbol', 'PB']]
    df = pd.merge(df, _df, on='symbol', how='inner')

    # 求ROE
    _df = get_fundamentals_without_limit(table='deriv_finance_indicator', symbols=symbol_list, start_date=last_day,
                                         end_date=last_day,
                                         fields="ROEAVG", filter="ROEAVG>0", df=True)
    print("got roe data")  # spend 72s
    _df = _df[['symbol', 'ROEAVG']]
    # df = pd.concat([df, _df], axis=1, index='symbol')
    df = pd.merge(df, _df, on='symbol', how='inner')
    df = df.rename(columns={'ROEAVG': 'ROE'})
    # df = df[(df['PB'] > 0) & (df['ROE'] > 0)]
    # df = df.query('PB > 2 and ROE > 0')
    df = df.dropna()

    # pb_ = df["PB"].values  # 这是Y
    # roe_ = df["ROE"].values  # 这是X
    symbol_list = get_symbol_list_by_delta_value(df, ["ROE"], "PB", "symbol")
    return symbol_list


# PB>0， ROEAVG>0
def get_target_list_by_pb_roe_test(input_list, now):
    last_day = get_previous_trading_date("SHSE", now)
    symbol_list = list(input_list)
    # symbol_list = filter_black_list(symbol_list, now)
    df = pd.DataFrame([])
    df["symbol"] = symbol_list
    df.to_excel(f"{now}-symbols-{str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.xlsx")
    factor_dict = {
        "ROEAVG": "ROEAVG > 0",
        "PB": "PB > 0",
        # "EBITMARGIN": "",
    }
    df = get_fundamentals_without_limit3(symbols=symbol_list, start_date=last_day, end_date=last_day,
                                         fields_and_filter=factor_dict, df=True)
    df = df.rename(columns={'ROEAVG': 'ROE'})

    # Step 4: query to filter
    # df = df[(df['PB'] > 0) & (df['ROE'] > 0)]
    # df = df.query('PB > 2 and ROE > 0')
    df = df.dropna()
    # pb_ = df["PB"].values  # 这是Y
    # roe_ = df["ROE"].values  # 这是X
    # 2.6011896486130346   0.44742775479595653
    symbol_list = get_symbol_list_by_delta_value(df, ["ROE"], "PB", "symbol")
    time_now = str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    df.to_excel(f"{now}-df-{time_now}.xlsx")
    return symbol_list



# 防守型策略
# 中证红利
def defensive_strategy(symbol_list, now):
    """
    排名条件设市盈率从小到大，权重2；  PETTM
    股息率从大到小，权重1； DY
    市净率从小到大，权重3； PB
    历史贝塔从小到大，权重2；
    自定义波动率指标从小到大权重10，
    """
    F_PETTM = "PETTM"
    F_DY = "DY"
    F_PB = "PB"
    tables = get_table_names_by_factors([F_PETTM, F_DY, F_PB])

    PETTM = fast_batch_get_neutralized_factor(symbol_list, tables[F_PETTM], F_PETTM, now, more_is_better=False)
    DY = fast_batch_get_neutralized_factor(symbol_list, tables[F_DY], F_DY, now, more_is_better=True)
    PB = fast_batch_get_neutralized_factor(symbol_list, tables[F_PB], F_PB, now, more_is_better=False)

    beta = {}
    volatility = {}

    for symbol in symbol_list:
        beta[symbol] = get_beta_weight_2(symbol, now, count=30)  # count=20
        volatility[symbol] = get_volatility_normal(symbol, now, count=30)  # count=60

    df = pd.DataFrame([])
    df["symbol"] = PETTM.keys()
    df["PETTM"] = PETTM.values()
    df["PB"] = PB.values()
    df["DY"] = DY.values()
    df["beta"] = beta.values()
    df["volatility"] = volatility.values()

    weight = [1, -1, -1, -1, -1]

    symbol_list = get_symbol_list_by_weight_score(df, weight, start=1)

    return symbol_list


def defensive_strategy2(symbol_list, now):
    """
    排名条件设市盈率从小到大，权重2；  PETTM
    股息率从大到小，权重1； DY
    市净率从小到大，权重3； PB
    历史贝塔从小到大，权重2；
    自定义波动率指标从小到大权重10，
    """
    factor_dict = {
        "PETTM": "",
        "DY": "",
        "PB": "",
    }

    df_with_factors = fast_batch_get_neutralized_factor2(symbol_list, now, factor_dict)

    beta = {}
    volatility = {}
    for symbol in df_with_factors["symbol"].values:
        beta[symbol] = get_beta_weight_2(symbol, now, count=30)  # count=20
        volatility[symbol] = get_volatility_normal(symbol, now, count=30)  # count=60
    df = pd.DataFrame([])
    df["symbol"] = df_with_factors["symbol"]
    df["PETTM"] = df_with_factors["PETTM"]
    df["PB"] = df_with_factors["PB"]
    df["DY"] = df_with_factors["DY"]
    df["beta"] = beta.values()
    df["volatility"] = volatility.values()

    weight = [1, -1, -1, -1, -1]
    symbol_list = get_symbol_list_by_weight_score(df, weight, start=1)
    return symbol_list



# 获取不同行业相关概念股数据集的相关性系数
def get_symbols_corr_list(code="", frequency="1d", count=250, end_time="2017-12-30", num=10):
    """
    获取不同行业相关概念股数据集的相关性系数
    :param code:
    :param frequency:
    :param count:
    :param end_time:
    :param num:
    :return:
    """
    symbols = get_concept(code)  # 查询概念股票列表
    df = pd.DataFrame()

    for symbol in symbols:
        try:
            data = history_n(symbol=symbol, frequency=frequency, count=count, end_time=end_time, fields="close",
                             fill_missing="last", adjust=ADJUST_PREV, df=True)
            if len(data) == count:
                data_close = pd.DataFrame({symbol: data["close"]})
                if len(df) == 0:
                    df = data_close
                else:
                    df = pd.concat([df, data_close], axis=1)
        except:
            pass

    return get_max_corr_list(df, num)


# 对相关性高度两支标的，进行协整性判断
def check_double_symbols(symbols_1, symbols_2, frequency="1d", count=250, end_time="2017-12-30"):
    symbols_1_data = history_n(symbol=symbols_1, frequency=frequency, count=count, end_time=end_time, fields="close",
                               fill_missing="last", adjust=ADJUST_PREV, df=True)
    symbols_2_data = history_n(symbol=symbols_2, frequency=frequency, count=count, end_time=end_time, fields="close",
                               fill_missing="last", adjust=ADJUST_PREV, df=True)

    symbols_1_close = symbols_1_data["close"]
    symbols_2_close = symbols_2_data["close"]

    x = symbols_1_close.values
    y = symbols_2_close.values

    # weight, bias = lr.linear_regression(x, y)
    const, weight = get_const_and_weight(x, y)

    y_ = weight * x + const

    d_value = y - y_

    st = sm.tsa.stattools.adfuller(d_value)
    if st[0] > st[4]['10%']:
        print('d_value存在单位根,为非平稳序列', symbols_1, "-", symbols_2, )
        return
    elif st[0] < st[4]['1%']:
        print('d_value没有单位根,为平稳序列')
    else:
        print("d_value无法判定", symbols_1, "-", symbols_2, )
        return

    mean = np.mean(d_value)  # 均值
    std = np.std(d_value)  # 方差

    t = sm.tsa.stattools.adfuller(d_value)
    output = pd.DataFrame(
        index=['Test Statistic value', 'p-value', 'Lags Used', 'Number of Observations Used', 'Critical Value(1%)',
               'Critical Value(5%)', 'Critical Value(10%)'], columns=['value'])
    output.iloc[0][0] = t[0]
    output.iloc[1][0] = t[1]
    output.iloc[2][0] = t[2]
    output.iloc[3][0] = t[3]
    output.iloc[4][0] = t[4]['1%']
    output.iloc[5][0] = t[4]['5%']
    output.iloc[6][0] = t[4]['10%']

    record_file = '配对交易结果' + '.csv'
    if t[1] < 0.05:
        print("可以配对:", symbols_1, "-", symbols_2, )

        res = [symbols_1, symbols_2, weight, const, mean, std]
        print(res)

        writer = csv.writer(open(record_file, 'a+', encoding='utf8', newline=''))
        writer.writerow(res)

    else:
        print("P-VALUE不合适", symbols_1, "-", symbols_2, )


# 这里使用的是使用股票收盘价与同期指数的绝对值进行回归
def get_beta_weight_1_not_support(symbol, now, count, market_index="SHSE.000001"):
    """
    一般用单个股票资产的历史收益率对同期指数（大盘）收益率进行回归，回归系数就是Beta系数。

    计算贝塔值和自定义的波动率
    低波策略又名防守策略，有两种计算方法，低beta 或者 低波动。
    低波动用日收益率的标准差（不是股价的标准差）。
    这样可以排除股价高低的影响。
    https://www.joinquant.com/post/7200?tag=algorithm
    """
    last_day = get_previous_trading_date("SHSE", now)
    market_data = history_n(symbol=market_index, frequency="1d", count=count,
                            end_time=last_day,
                            fields="high,low,close",
                            fill_missing="last")

    market_close = get_data_value(market_data, "close")

    symbol_data = history_n(symbol=symbol, frequency="1d", count=count,
                            end_time=last_day,
                            fields="high,low,close",
                            fill_missing="last")

    symbol_close = get_data_value(symbol_data, "close")

    const, weight = get_const_and_weight(market_close, symbol_close)
    return weight


# 这里使用的是收益进行计算
# 代表与大盘的联动波动率
def get_beta_weight_2(symbol, now, count, market_index="SHSE.000001"):
    """
    一般用单个股票资产的历史收益率对同期指数（大盘）收益率进行回归，回归系数就是Beta系数。
    """
    last_day = get_previous_trading_date("SHSE", now)
    market_data = history_n(symbol=market_index, frequency="1d", count=count,
                            end_time=last_day,
                            fields="high,low,close",
                            fill_missing="last")

    market_close = get_data_value(market_data, "close")

    market_close_ratio = []
    for i in range(1, len(market_close)):
        ratio = (market_close[i] - market_close[i - 1]) / market_close[i - 1]
        ratio = (0.99 ** (len(market_close) - i)) * ratio
        market_close_ratio.append(ratio)

    symbol_data = history_n(symbol=symbol, frequency="1d", count=count,
                            end_time=last_day,
                            fields="high,low,close",
                            fill_missing="last")

    symbol_close = get_data_value(symbol_data, "close")

    symbol_close_ratio = []
    for i in range(1, len(symbol_close)):
        ratio = (symbol_close[i] - symbol_close[i - 1]) / symbol_close[i - 1]
        ratio = (0.99 ** (len(market_close) - i)) * ratio
        symbol_close_ratio.append(ratio)

    const, weight = get_const_and_weight(market_close_ratio, symbol_close_ratio)
    return weight


# 一种波动率的方法，采用wind波动率计算法,不建议使用
def get_volatility_wind(symbol, now, count):
    """
    波动率来源：https://www.joinquant.com/post/10884?tag=algorithm
    貌似wind的公式
    :param symbol:
    :param now:
    :return:
    """
    last_day = get_previous_trading_date("SHSE", now)
    data = history_n(symbol=symbol, frequency="1d", count=count,
                     end_time=last_day, fields="high,low,close", fill_missing="last")

    close = get_data_value(data, "close")

    close = pd.DataFrame(close)
    stocks_change = close.apply(lambda x: np.log(x) - np.log(x.shift(1)))
    # 计算30,60,90日波动率,年化之
    daily_vol = stocks_change.std()
    annual_vol = daily_vol * 252 ** 0.5
    return annual_vol.values[0]


# 波动率的简单方法,感觉比wind的要好
def get_volatility_normal(symbol, now, count):
    last_day = get_previous_trading_date("SHSE", now)
    data = history_n(symbol=symbol, frequency="1d", count=count,
                     end_time=last_day, fields="high,low,close", fill_missing="last")
    close = get_data_value(data, "close")

    res = np.var(close) / np.mean(close)
    res = np.sqrt(res)
    return res


def buy_check(now, symbol):
    return buy_check_volume_increase_and_price_amplitude(now, symbol)


# 定义60天的波动率小于10%，完成以后可以改成
def buy_check_price_amplitude(now, symbol, count=60, threshold=0.1):
    last_day = get_previous_trading_date("SHSE", now)

    # amplitude = beta_and_vol.get_volatility_normal(symbol,last_day,count=count)

    data = history_n(symbol, frequency="1d", count=count, end_time=last_day, fields="open,high,low,close")
    close = get_data_value(data, "close")
    open = get_data_value(data, "open")
    high = get_data_value(data, "high")
    low = get_data_value(data, "low")

    amplitude = (np.max(high) - np.min(low)) / close[0]

    if amplitude < threshold:
        return True
    else:
        return False


# 买入点-地量（连续18周成交量小于最近4年内天量的10%）
def buy_check_mean_volume_small(now, symbol, week_count_short=18, week_count_long=150, threshold=0.1):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=week_count_long * 5, end_time=last_day, fields="volume")
    volume = get_data_value(data, "volume")
    max_volume_last = np.max(volume[-week_count_short * 5:])
    max_volume = np.max(volume)

    if max_volume_last < max_volume * 0.1:
        return True
    else:
        return False


# 单日成交量大于该股的前五日移动平均成交量2.5倍，大于前10日移动平均成交量3倍
def buy_check_volume_increase(now, symbol):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=11, end_time=last_day, fields="volume")
    volume = get_data_value(data, "volume")
    h = volume
    volume = h['volume'][-1]
    volume_mean_5 = np.mean(h['volume'][-6:-1])
    volume_mean_10 = np.mean(h['volume'][-11:-1])
    if volume > volume_mean_5 * 2.5 and volume > volume_mean_10 * 3:
        return True
    else:
        return False


# 找到昨天之前成交量大于昨天的成交量（0.8倍），这个区间的天数大于30天
# 昨天单日成交量大于该区间的平均成交量的2倍
# 区间价格波动小于10%
def buy_check_volume_increase_and_price_amplitude(now, symbol):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=270, end_time=last_day, fields="open,high,low,close,volume")

    close = get_data_value(data, "close")
    open = get_data_value(data, "open")
    high = get_data_value(data, "high")
    low = get_data_value(data, "low")
    volume = get_data_value(data, "volume")

    volume_yesterday = volume[-1]

    try:
        # 昨日收盘价要高于开盘价
        if close[-1] < open[-1]:
            return False
    except:
        return False

    # 找到昨天之前成交量大于昨天的成交量（0.8倍）的那个日期，这个日期到今天的区间的天数大于30天
    start = 0
    end = -1
    for i in range(1, len(volume)):
        index = -(i + 1)
        if volume[index] > volume[-1] * 0.8:
            start = index + 1
            break
    if start == 0 or (end - start) < 30:
        return False

    # 昨天单日成交量大于该区间的平均成交量的2倍
    volume_mean = np.mean(volume[start:end])
    volume_mean_5 = np.mean(volume[-6:-1])
    if volume_yesterday < volume_mean * 2.5 or volume_yesterday < volume_mean_5 * 2.5:
        return False

    # 区间价格波动小于10%
    price_max = max(high[start:end])
    price_min = min(low[start:end])
    price_amplitude = (price_max - price_min) / open[start]
    # print 'min=%s, max=%s, open=%s, amplitude=%s' % (price_min, price_max, h['open'][start], price_amplitude)
    if price_amplitude > 0.1:
        return False

    return True


# 卖出点判定
def sell_check(now, symbol):
    if sell_check_mean_price(now, symbol, 0.1) and sell_check_turnover_ratio(now, symbol):
        return True
    if sell_check_mean_price(now, symbol, 0.2):
        return True
    return False


# 卖出点-均线（5日线超过10日线10%，10日线超过30日线10%）
def sell_check_mean_price(now, symbol, threshold=0.1):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=31, end_time=last_day, fields="open,high,low,close,volume")

    close = get_data_value(data, "close")
    open = get_data_value(data, "open")
    high = get_data_value(data, "high")
    low = get_data_value(data, "low")
    volume = get_data_value(data, "volume")

    # 求5日线、10日线、30日线
    mean_5 = np.mean(close[-5:])
    mean_10 = np.mean(close[-10:])
    mean_30 = np.mean(close[-30:])
    diff_5_10 = (mean_5 - mean_10) / mean_10
    diff_5_30 = (mean_5 - mean_30) / mean_30
    diff_10_30 = (mean_10 - mean_30) / mean_30

    # 求昨天的求5日线、10日线、30日线
    yes_mean_5 = np.mean(close[-6:-1])
    yes_mean_10 = np.mean(close[-11:-1])
    yes_mean_30 = np.mean(close[-31:-1])
    yes_diff_5_10 = (yes_mean_5 - yes_mean_10) / yes_mean_10
    yes_diff_5_30 = (yes_mean_5 - yes_mean_30) / yes_mean_30
    yes_diff_10_30 = (yes_mean_10 - yes_mean_30) / yes_mean_30

    return diff_5_30 > threshold


# 卖出点-换手率
def sell_check_turnover_ratio(now, symbol):
    last_day = get_previous_trading_date("SHSE", now)
    # 换手率
    _df = get_fundamentals(table='trading_derivative_indicator', symbols=symbol, start_date=last_day,
                           end_date=last_day, fields='TURNRATE')

    TURNRATE = get_data_value(_df, "TURNRATE")
    return TURNRATE[0] > 15


def sell_check_rsrs(now, symbol):
    threshold = -0.7
    zscore_rightdev = get_rsrs_weight(symbol, now)

    if zscore_rightdev < threshold:
        return True
    else:
        return False


# 斜率越大，支撑相对强弱大，反之则小
def get_rsrs_weight(symbol, now, length=600, window=20):
    last_day = get_previous_trading_date("SZSE", now)
    last_last_day = get_previous_trading_date("SZSE", last_day)
    data = history_n(symbol=symbol, frequency="1d", count=length + window,
                     end_time=last_last_day,
                     fields="open,high,low,close",
                     fill_missing="last", df=True)
    data_high = (data["high"].values)
    data_low = (data["low"].values)

    # 这里是直到前天的RSRS序列值
    rsrs_weights = []

    for len_ in range(len(data) - window + 1):
        high_ = data_high[len_:len_ + window]
        low_ = data_low[len_:len_ + window]

        low_ = sm.add_constant(low_)
        model_ = sm.OLS(high_, low_)
        results_ = model_.fit()
        weight_ = (results_.params[1])

        # rsrs_weights.append(weight_)   #原始weight
        rsrs_weights.append(weight_)  # 这里是加上权重的weight

    last_day_data = history_n(symbol=symbol, frequency="1d", count=window, end_time=last_day,
                              fields="open,high,low,close", fill_missing="last", df=True)

    high_ = last_day_data["high"].values
    low_ = last_day_data["low"].values

    coefficient_determination = (np.corrcoef(high_, low_))[0][1] ** 2

    const, weight = get_const_and_weight(low_, high_)
    z_score = (weight - np.mean(rsrs_weights)) / np.std(rsrs_weights)

    # RSRS得分
    RSRS_socre = z_score * coefficient_determination
    return RSRS_socre


# 庄股值计算   庄股：能够无量涨停的或无量杀跌的。 庄股值：成为庄股的可能性
def cow_stock_value(now, symbol):
    _pb = get_fundamentals(table='trading_derivative_indicator', symbols=symbol, start_date=now,
                           end_date=now, fields='PB,NEGOTIABLEMV')
    pb = get_data_value(_pb, "PB")
    NEGOTIABLEMV = (get_data_value(_pb, "NEGOTIABLEMV"))[0] / 100000000

    if NEGOTIABLEMV > 100:
        return 0
    num_fall = fall_money_day_3line(now, symbol, 120, 20, 60, 160)
    num_cross = money_5_cross_60(now, symbol, 120, 5, 160)
    return (num_fall * num_cross) / (pb * (NEGOTIABLEMV ** 0.5))


# 3条移动平均线计算缩量
def fall_money_day_3line(now, symbol, n, n1=20, n2=60, n3=120):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=n + n3, end_time=last_day, fields="cum_volume")
    stock_m = get_data_value(data, "cum_volume")
    i = 0
    count = 0
    while i < n:
        money_MA200 = np.mean(stock_m[i:n3 - 1 + i])
        money_MA60 = np.mean(stock_m[i + n3 - n2:n3 - 1 + i])
        money_MA20 = np.mean(stock_m[i + n3 - n1:n3 - 1 + i])
        if money_MA20 <= money_MA60 and money_MA60 <= money_MA200:
            count = count + 1
        i = i + 1
    return count


# 计算脉冲（1.0版本） 成交额5日穿60日？
def money_5_cross_60(now, symbol, n, n1=5, n2=60):
    last_day = get_previous_trading_date("SHSE", now)

    data = history_n(symbol, frequency="1d", count=n + n2 + 1, end_time=last_day, fields="cum_volume")
    stock_m = get_data_value(data, "cum_volume")
    i = 0
    count = 0
    while i < n:
        money_MA60 = np.mean(stock_m[i + 1:n2 + i])
        money_MA60_before = np.mean(stock_m[i:n2 - 1 + i])
        money_MA5 = np.mean(stock_m[i + 1 + n2 - n1:n2 + i])
        money_MA5_before = np.mean(stock_m[i + n2 - n1:n2 - 1 + i])
        if (money_MA60_before - money_MA5_before) * (money_MA60 - money_MA5) < 0:
            count = count + 1
        i = i + 1
    return count


# #在symbol中进行中性化因子处理
def get_neutralized_factor(symbol, table_name, factor, symbol_list, now):
    """
    下面是开始对行业中性化的处理：
    具体方法：根据大部分的研报对于中性化的处理，主要的方法是利用回归得到一个与风险因子线性无关的因子，
    即通过建立线性回归，提取残差作为中性化后的新因子。这样处理后的中性化因子与风险因子之间的相关性严格为零。
     :param symbol:
     :param table_name: str or NAN
     :param factor:
     :param symbol_list:
     :param now:
     :return:
     """
    last_day = get_previous_trading_date("SHSE", now)

    _symbol_list = symbol_list
    symbol_list = []
    for _ in _symbol_list:
        symbol_list.append(_)

    # 根据市值进行中性化处理
    df = get_fundamentals(table='trading_derivative_indicator', symbols=symbol_list, start_date=last_day,
                          end_date=last_day, fields="TOTMKTCAP", df=True)
    df = df.dropna()
    df = df.sort_values(["symbol"])

    if not table_name:
        table_name, factor = get_table_name_by_factor(factor)

    df[factor] = 0
    for _ in range(len(df)):
        _symbol = df.iloc[_, 0]
        # 获取每股净资产
        _df = get_fundamentals(table=table_name, symbols=_symbol, start_date=last_day,
                               end_date=last_day, fields=factor, df=True)
        try:
            df.iloc[_, 4] = _df[factor].values
        except:
            df.iloc[_, 4] = 0

    df = df[df[factor] > 0]

    TOTMKTCAP = df["TOTMKTCAP"].values  # 这个是x
    NAPSNEWP = df[factor].values  # 这个是Y

    df = get_fundamentals(table='trading_derivative_indicator', symbols=symbol, start_date=last_day,
                          end_date=last_day, fields="TOTMKTCAP", df=True)
    _x = df["TOTMKTCAP"].values  # symbol的市值
    _df = get_fundamentals(table=table_name, symbols=symbol, start_date=last_day,
                           end_date=last_day, fields=factor, df=True)
    _Y = _df[factor].values  # 待求的因子值

    const, weight = get_const_and_weight(TOTMKTCAP, NAPSNEWP)
    d_value = _Y - (weight * _x + const)
    return round(d_value[0], 2)


# 在symbol中进行 因子中性化 处理
def fast_batch_get_neutralized_factor(symbol_list, table_name, factor, now, more_is_better):
    """
    以总市值TOTMKTCAP为基准，对因子做中性化处理
    :param symbol_list:
    :param table_name: str or NAN
    :param factor:
    :param now:
    :param more_is_better: 这个指的是因子本身，而不是计算出的值
    :return:
    """
    last_day = get_previous_trading_date("SHSE", now)
    _symbol_list = symbol_list
    symbol_list = []
    for _ in _symbol_list:
        symbol_list.append(_)
    TOTMKTCAP = []  # 总市值
    # 根据市值进行中性化处理
    data = get_fundamentals(table='trading_derivative_indicator', symbols=symbol_list, start_date=last_day,
                            end_date=last_day, fields="TOTMKTCAP")

    if len(data) == len(symbol_list):
        for _ in data:
            try:
                TOTMKTCAP.append(_["TOTMKTCAP"])
            except:
                TOTMKTCAP.append(1e+15)
    else:
        for symbol in symbol_list:
            try:
                _data = get_fundamentals(table='trading_derivative_indicator', symbols=symbol, start_date=last_day,
                                         end_date=last_day, fields="TOTMKTCAP")

                TOTMKTCAP.append(_data[0]["TOTMKTCAP"])
            except:
                TOTMKTCAP.append(1e+15)

    factor_value_list = []
    if not table_name:
        table_name, factor = get_table_name_by_factor(factor)
    data = get_fundamentals(table=table_name, symbols=symbol_list, start_date=last_day,
                            end_date=last_day, fields=factor)

    if len(data) == len(symbol_list):
        for _ in data:
            try:
                factor_value_list.append(_[factor])
            except:

                if more_is_better == True:
                    factor_value_list.append(-999)
                else:
                    factor_value_list.append(999)
    else:
        for symbol in symbol_list:
            try:
                _data = get_fundamentals(table=table_name, symbols=symbol, start_date=last_day,
                                         end_date=last_day, fields=factor)
                factor_value_list.append(_data[0][factor])
            except:

                if more_is_better == True:
                    factor_value_list.append(-999)
                else:
                    factor_value_list.append(999)

    TOTMKTCAP = fast_delta_edge(TOTMKTCAP)  # 这个是x
    factor_value_list = fast_delta_edge(factor_value_list)  # 这个是Y

    const, weight = get_const_and_weight(TOTMKTCAP, factor_value_list)

    # 因子的deta_value值，即因子对应数值与回归线的差值
    d_value_dict = {}
    for i in range(len(symbol_list)):
        d_value = factor_value_list[i] - (weight * TOTMKTCAP[i] + const)
        d_value_dict[symbol_list[i]] = d_value

    return d_value_dict


# 在symbol中进行 因子中性化 处理
def fast_batch_get_neutralized_factor2(symbol_list, now, factor_dict: dict, base_factor="TOTMKTCAP"):
    """
    以总市值TOTMKTCAP为基准，对因子做中性化处理
    :param symbol_list:
    :param factor_dict:
    :param now:
    :param base_factor:
    :return:
    """
    last_day = get_previous_trading_date("SHSE", now)
    symbol_list = list(symbol_list)
    all_factor_dict = {
        # "TOTMKTCAP": "",
        # "PETTM": "PETTM > 0",
        # "DY": "",
        # "PB": "",
    }
    all_factor_dict.update({base_factor: ""})
    all_factor_dict.update(factor_dict)

    df = get_fundamentals_without_limit3(symbols=symbol_list, start_date=last_day, end_date=last_day,
                                         fields_and_filter=all_factor_dict, df=True)
    # Step 4: query to filter if needed
    # df = df.query('PB > 2 and ROE > 0')
    df = df.dropna()
    df[base_factor] = fast_delta_edge(df[base_factor].to_list())  # 这个是x
    for factor in factor_dict:
        df[factor] = fast_delta_edge(df[factor].to_list())  # 这个是Y
        # df["d_value_" + factor] replace df[factor]
        df[factor] = get_delta_value_list(df, [base_factor], factor)
    return df


def get_predict_close(symbol, now, count):
    last_day = get_previous_trading_date("SHSE", now)
    data = history_n(symbol, frequency="1d", end_time=last_day, count=count, fields="close,open", df=True)
    close = data["close"].values
    open = data["open"].values
    const, weight = get_const_and_weight(open, close)
    return const, weight


def market_value_weighted(stocks, MV, BM):
    select = stocks[(stocks.NEGOTIABLEMV == MV) & (stocks.BM == BM)]
    market_value = select['mv'].values
    mv_total = np.sum(market_value)
    mv_weighted = [mv / mv_total for mv in market_value]
    stock_return = select['return'].values
    # 返回市值加权的收益率的和
    return_total = []
    for i in range(len(mv_weighted)):
        return_total.append(mv_weighted[i] * stock_return[i])
    return_total = np.sum(return_total)
    return return_total


def get_time_Ymd(dt: datetime):
    """
    transfer "2024-07-31 09:31:00+08:00" to "2024-07-31"
    :param dt:
    :return:
    """
    # original_datetime_str = "2024-07-31 09:31:00+08:00"
    # dt = datetime.strptime(original_datetime_str, "%Y-%m-%d %H:%M:%S%z")
    # remove timezone
    dt_no_timezone = dt.replace(tzinfo=None)
    # dt_no_timezone_str = dt_no_timezone.strftime("%Y-%m-%d %H:%M:%S")
    dt_no_timezone_str = dt_no_timezone.strftime("%Y-%m-%d")
    return dt_no_timezone_str
