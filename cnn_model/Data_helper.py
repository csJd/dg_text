#coding=utf-8
import pandas as pd
import numpy as np
#
#
def load_data_and_labels(train_file):

    # train_file = "../processed_data/splited_train_data.csv"

    x_text = []
    y = []

    with open(train_file,'r',encoding='utf-8') as f:
        for line in f.readlines():
            row = line.strip().split(',')
            x_text.append(row[1])
            train_label = int(row[0])

            #构造label
            label = [0] * 19
            label[train_label-1] = 1
            y.append(label)

    return x_text,y

'''
    获取分好词的文件
'''
def get_predict_data(filename):
    '''
    :param filename: 分好词，需要预测的文件
        default:./dev_processed_data/shuffle_test_data.csv
    :return: 一个字符串数组
    '''

    pd_data = pd.read_csv(filename, sep=",")
    contexts = []
    for index, row in pd_data.iterrows():
        context = row[2]
        contexts.append(context)

    return contexts


def batch_iter(data, batch_size, num_epochs, shuffle=True):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int((len(data)-1)/batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        if shuffle:
            shuffle_indices = np.random.permutation(np.arange(data_size))
            shuffled_data = data[shuffle_indices]
        else:
            shuffled_data = data
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]

