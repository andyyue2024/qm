from datetime import datetime

import matplotlib.pyplot as plot

from Tools.qmtools.math_tools import *


# 对当前全部标的的PB-ROE可视化
def show_pb_roe(file_name):
    # df = pd.read_excel("10-5-df.dropna-2024-08-11.xlsx")
    df = pd.read_excel(file_name)
    # df = df[(df['PB'] > 0) & (df['ROE'] > 0)]
    df = df.query('PB < 70 and ROE < 40')
    pb_ = df["PB"].values  # 这是Y
    roe_ = df["ROE"].values  # 这是X

    roe = []
    roe.extend(roe_)
    pb = []
    pb.extend(pb_)

    plot.xlim(0, 40)
    plot.ylim(0, 70)
    show_x_y(roe, pb, file_name, "ROE", "PB")


def show_x_y(xx, yy, title=None, xlabel=None, ylabel=None, is_save=False):
    const, weight = get_const_and_weight(xx, yy)
    print(const, " ", weight)
    pre_yy = const + weight * np.array(xx)
    plot.scatter(xx, yy)
    plot.title(title)
    plot.xlabel(xlabel)
    plot.ylabel(ylabel)
    # plt.plot(upperband, "r--", close, "b", lowerband, "r--")
    plot.plot(xx, pre_yy, "r-")
    if is_save:
        plot.savefig(f"{title}-{ylabel}-{xlabel}-{str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))}.png")
    plot.show()
