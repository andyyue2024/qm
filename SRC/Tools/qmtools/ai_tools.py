import tensorflow as tf
import numpy as np
import pandas as pd
from gm.api import *


# 使用TensorFLow的逻辑回归
def get_check_flag(symbol, now):
    last_day = get_previous_trading_date("SHSE", now)
    last_last_day = get_previous_trading_date("SHSE", last_day)

    df = history_n(symbol, frequency="1d", end_time=last_last_day, count=60, fields="open,close,high,low,volume",
                   df=True)

    df["flag"] = 0

    for _ in range(1, len(df)):
        res = (df.loc[_ - 1, "close"]) - (df.loc[_ - 1, "open"])
        if (res) > 0:
            df.loc[_, "flag"] = 1

    train_x, train_y = df, df.pop('flag')

    symbol_feature_columns = []
    for key in train_x.keys():
        symbol_feature_columns.append(tf.feature_column.numeric_column(key=key))

    classifier = tf.estimator.DNNClassifier(
        # 这个模型接受哪些输入的特征
        feature_columns=symbol_feature_columns,
        # 包含两个隐藏层，每个隐藏层包含10个神经元.
        hidden_units=[128, 128, 128],
        # 最终结果要分成的几类
        n_classes=2)

    def train_func(train_x, train_y):
        dataset = tf.data.Dataset.from_tensor_slices((dict(train_x), train_y))
        dataset = dataset.shuffle(1000).repeat().batch(100)
        return dataset

    classifier.train(
        input_fn=lambda: train_func(train_x, train_y),
        steps=1000)

    def predict_input_fn(features, labels, batch_size):
        features = dict(features)
        if labels is None:
            # No labels, use only features.
            inputs = features
        else:
            inputs = (features, labels)
        dataset = tf.data.Dataset.from_tensor_slices(inputs)

        assert batch_size is not None, "batch_size must not be None"
        dataset = dataset.batch(batch_size)
        return dataset

    df = history_n(symbol, frequency="1d", end_time=last_day, count=1, fields="open,close,high,low,volume", df=True)
    test = [df["open"].values, df["close"].values, df["high"].values, df["low"].values, df["volume"].values]

    test_data = pd.DataFrame({'open': test[0], 'close': test[1], 'high': test[2], 'low': test[3], 'volume': test[4]},
                             index=[0])

    predict_result = []
    predictions = classifier.predict(
        input_fn=lambda: predict_input_fn(test_data, labels=None, batch_size=1))
    for predict in predictions:
        predict_result.append(predict['probabilities'].argmax())

    return (predict_result)


def get_check_flag2(symbol, now):
    last_day = get_previous_trading_date("SHSE", now)
    last_last_day = get_previous_trading_date("SHSE", last_day)

    df = history_n(symbol, frequency="1d", end_time=last_last_day, count=60, fields="open,close,high,low,volume",
                   df=True)

    df["flag"] = 0

    for _ in range(1, len(df)):
        res = (df.loc[_ - 1, "close"]) - (df.loc[_ - 1, "open"])
        if (res) > 0:
            df.loc[_, "flag"] = 1

    train_x, train_y = df, df.pop('flag')

    symbol_feature_columns = []
    for key in train_x.keys():
        symbol_feature_columns.append(tf.feature_column.numeric_column(key=key))

    classifier = tf.estimator.DNNClassifier(
        # 这个模型接受哪些输入的特征
        feature_columns=symbol_feature_columns,
        # 包含两个隐藏层，每个隐藏层包含10个神经元.
        hidden_units=[128, 128, 128],
        # 最终结果要分成的几类
        n_classes=2)

    def train_func(train_x, train_y):
        dataset = tf.data.Dataset.from_tensor_slices((dict(train_x), train_y))
        dataset = dataset.shuffle(1000).repeat().batch(100)
        return dataset

    classifier.train(
        input_fn=lambda: train_func(train_x, train_y),
        steps=1000)

    def predict_input_fn(features, labels, batch_size):
        features = dict(features)
        if labels is None:
            # No labels, use only features.
            inputs = features
        else:
            inputs = (features, labels)
        dataset = tf.data.Dataset.from_tensor_slices(inputs)

        assert batch_size is not None, "batch_size must not be None"
        dataset = dataset.batch(batch_size)
        return dataset

    df = history_n(symbol, frequency="1d", end_time=last_day, count=1, fields="open,close,high,low,volume", df=True)
    test = [df["open"].values, df["close"].values, df["high"].values, df["low"].values, df["volume"].values]

    test_data = pd.DataFrame({'open': test[0], 'close': test[1], 'high': test[2], 'low': test[3], 'volume': test[4]},
                             index=[0])

    predict_result = []
    predictions = classifier.predict(
        input_fn=lambda: predict_input_fn(test_data, labels=None, batch_size=1))
    for predict in predictions:
        predict_result.append(predict['probabilities'].argmax())

    return (predict_result[0])


# Tensorflow批量单线性回归_双变量
def linear_regression(real_B, real_A):
    real_A = np.reshape(real_A, (-1, 1))
    real_B = np.reshape(real_B, (-1, 1))

    x_ = tf.placeholder(tf.float32, [None, 1])
    y_ = tf.placeholder(tf.float32, [None, 1])  # y_为测试集结果数据

    weight = tf.Variable(tf.ones([1, 1]))
    bias = tf.Variable(tf.ones([1]))

    y = tf.matmul(x_, weight) + bias

    loss = tf.reduce_mean(tf.square(y - y_))  # 批量线性回归用这个损失函数
    train_step = tf.train.AdamOptimizer(0.0001).minimize(loss)

    init = tf.global_variables_initializer()

    flag = True
    with tf.Session() as sess:
        sess.run(init)

        count = 0
        loss_temp = 0
        while flag:

            feed = {x_: real_A, y_: real_B}
            sess.run(train_step, feed_dict=feed)

            loss_res = sess.run(loss, feed_dict=feed)

            if loss_temp == loss_res:
                flag = False
            count += 1
            loss_temp = loss_res

        weight = sess.run(weight)
        bias = sess.run(bias)

        return weight[0][0], bias[0]


# 单股票的逻辑回归分析
# Logistic regression analysis of a single stock
def linear_regression2(B, A):
    # 创建模拟数据
    # np.random.seed(0)
    # A = np.random.rand(100).astype(np.float32)
    # B = np.random.rand(100).astype(np.float32)
    y = 2 * A + 3 * B + 5 + np.random.normal(0, 2, len(A))  # y = 2A + 3B + 5 + 噪声

    # 将A和B组合成一个特征矩阵
    X = np.column_stack((A, B))

    # 定义模型
    class LinearModel(tf.keras.Model):
        def __init__(self):
            super(LinearModel, self).__init__()
            self.dense = tf.keras.layers.Dense(units=1, input_shape=[2])

        def call(self, inputs):
            return self.dense(inputs)

    # 创建模型实例
    model = LinearModel()

    # 损失函数和优化器
    loss_fn = tf.keras.losses.MeanSquaredError()
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)

    # 训练模型
    for i in range(100):
        with tf.GradientTape() as tape:
            predictions = model(X)
            loss = tf.reduce_mean(loss_fn(y, predictions))
        gradients = tape.gradient(loss, model.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))

        if i % 10 == 0:
            print(f"Epoch {i}, Loss: {loss.numpy()}")

    # 获取权重和偏置
    weights, bias = model.layers[0].get_weights()
    # print(f"Weights: {weights[0]}, Bias: {bias[0]}")
    return weights, bias
