import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import mean_squared_error

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

plt_title = "RNN+FC1 predictions for 《人民的名义》"
Datadir = "E:\PyCharmProjects\MasonicDLv0.1\Database\Renmindemingyi.csv"
Data_Sheet = "Sheet1"

with tf.name_scope(name='Hyperparameter'):
    early_stopping_rate = 0.001
    train_step = 3000
    global_step = tf.Variable(0, name="global_step")
    learning_rate = tf.train.exponential_decay(
        learning_rate=0.001,
        global_step=global_step,
        decay_steps=100,
        decay_rate=0.9,
        staircase=True)

regularizer_enabled = False
reg_rate = 0.05
hidden_layer_size = 30
seq_size = 10
test_size = 5

with tf.name_scope(name='Placeholder'):
    X = tf.placeholder(tf.float32, [None, seq_size, 1])
    Y = tf.placeholder(tf.float32, [None, seq_size])

    W = {
        'w1': tf.Variable(tf.random_normal([hidden_layer_size, 15])),
        'w2': tf.Variable(tf.random_normal([15, 1])),
        'w3': tf.Variable(tf.random_normal([10, 1])),
        "b1": tf.Variable(tf.random_normal([1])),
        "b2": tf.Variable(tf.random_normal([1])),
        "b3": tf.Variable(tf.random_normal([1]))
    }

with tf.name_scope(name='DataProcessing'):
    def normal(data):
        data = (data - data.min()) / (data.max() - data.min())
        return data


    data = pd.read_csv(Datadir, header=None)

    data = normal(data)
    data = np.array(data)
    data_size = np.shape(data)[0]

    seq, pre = [], []
    for i in range(data_size - seq_size + 1 - 1):
        seq.append(data[i: i + seq_size])
        pre.append(data[i + 1:i + seq_size + 1])

    data_size = data_size - seq_size + 1 - 1
    test_size = int(data_size * test_size)
    trX = seq[:data_size - test_size]
    trY = pre[:data_size - test_size]
    teX = seq[data_size - test_size:]
    teY = pre[data_size - test_size:]
    realY = data[-test_size:]
with tf.name_scope(name='NeuralNetwork'):
    def rnn(X, W):
        w1, w2, w3 = W['w1'], W['w2'], W['w3']
        b1, b2, b3 = tf.expand_dims(W['b1'], axis=0), tf.expand_dims(W['b2'], axis=0), W['b3']
        w1 = tf.tile(input=tf.expand_dims(w1, axis=0), multiples=[tf.shape(X)[0], 1, 1])
        w2 = tf.tile(input=tf.expand_dims(w2, axis=0), multiples=[tf.shape(X)[0], 1, 1])
        b1 = tf.tile(input=tf.expand_dims(b1, axis=1), multiples=[tf.shape(X)[0], 1, 1])
        b2 = tf.tile(input=tf.expand_dims(b2, axis=1), multiples=[tf.shape(X)[0], 1, 1])

        cell = tf.nn.rnn_cell.BasicRNNCell(hidden_layer_size)
        outputs, states = tf.nn.dynamic_rnn(cell, X, dtype=tf.float32)
        fc1 = tf.nn.tanh(tf.matmul(outputs, w1) + b1)
        # y_[batch_size, seq_size, hidden_layer_size]
        fc2 = tf.nn.tanh(tf.matmul(fc1, w2) + b2)
        fc2 = tf.squeeze(fc2)
        y_ = tf.nn.tanh(tf.matmul(fc2, w3) + b3)

        return y_

with tf.name_scope(name='TrainSettings'):
    y_ = rnn(X, W)
    loss = tf.reduce_mean(tf.square(Y - y_))
    train_op = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    prev_loss = 0
    for step in range(train_step):
        _, train_loss = sess.run([train_op, loss], feed_dict={X: trX, Y: trY})
        if step % 100 == 0 and prev_loss != -1:
            delta = 1 if prev_loss == 0 else (abs(train_loss - prev_loss) / prev_loss)
            prev_loss = train_loss

            prev_seq = teX[0]
            predict = []
            for i in range(test_size):
                next_seq = sess.run(y_, feed_dict={X: [prev_seq]})
                predict.append(next_seq[-1])
                prev_seq = np.vstack((prev_seq[1:], next_seq[-1]))
            test_loss = mean_squared_error(predict, realY)
            print("Train Step={0}".format(step))
            print("Train RMSE={0}".format(pow(train_loss, 0.5)))
            print("Test RMSE={0}".format(pow(test_loss, 0.5)))

            if delta < early_stopping_rate:
                prev_loss = -1
                break
        elif step == train_step - 1:
            pre_train = sess.run(y_, feed_dict={X: trX})[:, -1]

            prev_seq = teX[0]
            predict = []
            for i in range(test_size):
                next_seq = sess.run(y_, feed_dict={X: [prev_seq]})
                predict.append(next_seq[-1])
                prev_seq = np.vstack((prev_seq[1:], next_seq[-1]))

            pre = np.append(pre_train, np.array(predict))
            # pre = pre_train.append(np.array(predict))

            real_train = np.array(trY)[:, -1]

            real = np.append(real_train, realY)
            x_axis = np.arange(0, np.shape(real)[0])

            plt.figure(figsize=(16, 10))
            plt.vlines(data_size - test_size, 0, 1, colors="c", linestyles="dashed", label='train/test split')
            plt.plot(x_axis, pre, label="Prediction")
            plt.plot(x_axis, real, label="Observation")
            plt.legend()
            plt.title(plt_title)
            plt.show()
        elif train_loss < 0.0009:
            pre_train = sess.run(y_, feed_dict={X: trX})[:, -1]

            prev_seq = teX[0]
            predict = []
            for i in range(test_size):
                next_seq = sess.run(y_, feed_dict={X: [prev_seq]})
                predict.append(next_seq[-1])
                prev_seq = np.vstack((prev_seq[1:], next_seq[-1]))

            pre = np.append(pre_train, np.array(predict))
            # pre = pre_train.append(np.array(predict))

            real_train = np.array(trY)[:, -1]

            real = np.append(real_train, realY)
            x_axis = np.arange(0, np.shape(real)[0])

            plt.figure(figsize=(16, 10))
            plt.vlines(data_size - test_size, 0, 1, colors="c", linestyles="dashed", label='train/test split')
            plt.plot(x_axis, pre, label="Prediction")
            plt.plot(x_axis, real, label="Observation")
            plt.legend()
            plt.title(plt_title)
            plt.show()
