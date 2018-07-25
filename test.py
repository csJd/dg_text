#coding=utf-8
import collections
import numpy as np
import pickle as pk
import tensorflow as tf

# 查询训练集基本信息
# 训练集中 共有102278个训练样本
# 共有19个分类
# 句子的最大长度为：16000以上
# 词典个数：16097

def test1():

    filename = "./processed_data/phrase_level_data.csv"
    line_count = 0
    with open(filename,'r',encoding='utf-8') as f:

        for line in f.readlines():
            line_count+= 1

    f.close()
    print(line_count)
    pass

def test2():

    d = {'a':1,'b':4,'c':2}
    sorted_tuple = sorted(d.items(), key=lambda x: x[1], reverse=False)
    print(sorted_tuple)

def test3():
    A = np.array([[1, 2, 3], [4, 5, 6]])
    x = tf.transpose(A, [1, 0])
    print(A.shape)
    B = np.array([[[1, 2, 3], [4, 5, 6]]])
    y = tf.transpose(B, [2, 1, 0])

    with tf.Session() as sess:
        print(sess.run(x).shape)




if __name__ == "__main__":
    test3()
