"""
gm table tools help to deal with table params.

Step 1: create table and factor dict.
-------------
input:
{ASSLIABRT: "ASSLIABRT < 1", PETTM: "PETTM < 27 and PETTM > 0",}

return:
{
deriv_finance_indicator:      {
                                ASSLIABRT: "ASSLIABRT < 1",
                                EBITMARGIN: "EBITMARGIN > 60",
                              }

trading_derivative_indicator: {
                                PETTM: "PETTM < 27 and PETTM > 0",
                                PB: "PB < 10 and PB > 0",

                              }
}


Step 2: call get_fundamentals() with different tables .
-------------
input: table and factor dict

return: df


Step 3: merge df
-------------
df.concat()


Step 4: query to filter
-------------
df.query()


"""
from os import path


def load_factor_with_table():
    ret_factor_with_table = {}
    file_name = path.join(path.dirname(path.abspath(__file__)), "gm_table_and_fields.txt")
    for line in open(file_name, 'r', encoding='utf-8-sig'):
        line = line.strip('\n')[0:]
        lines = line.split(",")
        ret_factor_with_table[lines[1]] = lines[0]
    return ret_factor_with_table


# preload when import this module
factor_with_table = load_factor_with_table()


# result: (table_name, factor)
def get_table_name_by_factor(factor):
    global factor_with_table
    table_name = factor_with_table[factor]
    return table_name, factor


# result: {ASSLIABRT: "deriv_finance_indicator",EBITMARGIN: "deriv_finance_indicator"}
def get_table_names_by_factors(factors):
    global factor_with_table
    ret = {}
    for factor in factors:
        table_name = factor_with_table[factor]
        ret[factor] = table_name
    return ret


# Step1: create table and factor dict
def get_table_and_factor_dict(input_factor_dict: dict):
    global factor_with_table
    ret = {}
    for factor, value in input_factor_dict.items():
        table_name = factor_with_table[factor]
        inner_dict = {}
        if table_name in ret:
            inner_dict = ret.get(table_name)
        inner_dict[factor] = value
        ret[table_name] = inner_dict
    return ret


def get_fields_and_filters(input_dict: dict):
    KEY_SEP = ", "
    VALUE_SEP = " and "
    keys_str = ""
    values_str = ""
    for key, value in input_dict.items():
        keys_str += str(key) + KEY_SEP
        if len(str(value).strip()) != 0:
            values_str += str(value) + VALUE_SEP
    keys_str = keys_str.rstrip(KEY_SEP)
    values_str = values_str.rstrip(VALUE_SEP)
    return keys_str, values_str


if __name__ == "__main__":
    # print(globals())
    # factor_dict = {
    #     "ASSLIABRT": "ASSLIABRT < 1",
    #     "PETTM": "PETTM < 27 and PETTM > 0",
    #     "EBITMARGIN": "EBITMARGIN > 60",
    #     "PB": "PB < 10 and PB > 0",
    # }
    # ret1 = get_table_and_factor_dict(factor_dict)
    # print(ret1)
    pass
