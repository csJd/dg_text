# coding: utf-8
# created by Pengpeng on 2018/7/22
import pickle as pk
from utils.path_util import from_project_root
from utils.data_util import train_dev_split

# 根据各种权重，过滤语料中的词语
def filter_words(tf_pickle,bdc_pickle,tf_bdc_picle,df_pickle,lf_pickle,vocab_pickle):
    """
    Args:
        tf_pickle: tf文件路径
        bdc_pickle:  bdc文件路径
        tf_bdc_picle: tf_bdc文件路径
        vocab_pickle: 词典
    Returns:

    """
    # 加载权重文件
    tf_dict = pk.load(open(tf_pickle,'rb'))
    bdc_dict = pk.load(open(bdc_pickle,'rb'))
    tf_bdc_dict = pk.load(open(tf_bdc_picle,'rb'))
    vocab_dict = pk.load(open(vocab_pickle,'rb'))
    df_dict = pk.load(open(df_pickle,'rb'))
    lf_dict = pk.load(open(lf_pickle,'rb'))

    # 过滤条件 = 查询
    del_count = 0
    for (word,word_id) in vocab_dict.items():

        if tf_dict[word] <= 20 and bdc_dict[word] == 1:
            del_count += 1
        elif bdc_dict[word] < 0.1:
            del_count += 1
        elif tf_bdc_dict[word] > 300:
            del_count += 1
        elif tf_dict[word] == lf_dict[word]:
            del_count += 1
        elif lf_dict[word] >= 2 and tf_dict[word] < (lf_dict[word] * 2):
            del_count += 1
        elif df_dict[word] <= 500 and lf_dict[word] >= 2:
            del_count += 1

    print(del_count)

def pre_processed_data(data_file,tf_pickle,bdc_pickle,tf_bdc_picle,df_pickle,lf_pickle,filted_data_file):

    # 加载权重文件
    tf_dict = pk.load(open(tf_pickle, 'rb'))
    bdc_dict = pk.load(open(bdc_pickle, 'rb'))
    tf_bdc_dict = pk.load(open(tf_bdc_picle, 'rb'))
    df_dict = pk.load(open(df_pickle,'rb'))
    lf_dict = pk.load(open(lf_pickle,'rb'))

    empty_list_count = 0
    with open(data_file,'r',encoding='utf-8') as f,open(filted_data_file,'w',encoding='utf-8') as wf:
        for line in f.readlines():
            line_list = line.strip().split(',')
            label = line_list[0]
            word_list = line_list[1].strip().split()

            filtered_word_list = process_sen(tf_dict,bdc_dict,tf_bdc_dict,df_dict,lf_dict,word_list)

            if len(filtered_word_list) == 0 :
                empty_list_count += 1
                filtered_word_list = word_list
                print("empty_list:{}".format(empty_list_count))


            wf.write("{},{}\n".format(label," ".join(filtered_word_list)))

    pass

def process_sen(tf_dict,bdc_dict,tf_bdc_dict,df_dict,lf_dict,word_list):

    filtered_word_list = []
    for word in word_list:

        if tf_dict[word] <= 20 and bdc_dict[word] == 1:
            continue
        elif bdc_dict[word] < 0.1:
            continue
        elif tf_bdc_dict[word] > 300:
            continue
        elif tf_dict[word] == lf_dict[word]:
            continue
        elif lf_dict[word] >= 2 and tf_dict[word] < (lf_dict[word] * 2):
            continue
        elif df_dict[word] <= 500 and lf_dict[word] >= 2:
            continue
        filtered_word_list.append(word)

    return filtered_word_list
    pass


# 将pk文件转化为csv文件 【排序】
def  transfer_pk_to_csv(pickle_file,save_csv_file):

    data_dict = pk.load(open(pickle_file,'rb'))

    sorted_tuple = sorted(data_dict.items(), key=lambda x: x[1], reverse=False)

    with open(save_csv_file,'w',encoding='utf-8') as f:

        for (word,value) in sorted_tuple:

            f.write("{},{}\n".format(word,value))

# 将原训练文件，提取对应的列
def extract_data(train_file,extract_index,save_file):
    """
    Args:
        train_file: train_set.csv
        extract_index:  [3,2] : phrase_level and [3,1] : word_level
        save_file:
    Returns:
    """
    with open(train_file,'r',encoding='utf-8') as f,open(save_file,'w',encoding='utf-8') as wf:
        for line in f.readlines()[1:]:
            line_list = line.strip().split(',')

            for i in range(len(extract_index)):
                wf.write(line_list[extract_index[i]])
                if i < len(extract_index)-1:
                    wf.write(",")

            wf.write("\n")



def main():

    # extract data
    # extract_data(from_project_root("data/train_set.csv"),[3,2],
    #              from_project_root("lstm_model/processed_data/phrase_level_data.csv"))
    # exit()

    # 划分数据集
    # train_dev_split(from_project_root("lstm_model/processed_data/phrase_level_data.csv"))
    # exit()

    tf_pickle = from_project_root("processed_data/phrase_level_tf.pk")
    bdc_pickle = from_project_root("processed_data/phrase_level_bdc.pk")
    tf_bdc_picle = from_project_root("processed_data/phrase_level_tfbdc.pk")
    df_pickle = from_project_root("processed_data/phrase_level_df.pk")
    lf_pickle = from_project_root("processed_data/phrase_level_lf.pk")
    vocab_pickle = from_project_root("processed_data/phrase_level_word_dict.pk")

    # transfer_tf
    # transfer_pk_to_csv(df_pickle,from_project_root("cnn_model/processed_data/phrase_level_df.csv"))
    # filter_words(tf_pickle, bdc_pickle, tf_bdc_picle, vocab_pickle)

    data_file = from_project_root("processed_data/phrase_level_data.csv")
    filtered_data_file = from_project_root("cnn_model/processed_data/filtered_data_file")
    pre_processed_data(data_file,tf_pickle,bdc_pickle,tf_bdc_picle,df_pickle,lf_pickle,filtered_data_file)

    # filter_words(tf_pickle, bdc_pickle, tf_bdc_picle, df_pickle, lf_pickle, vocab_pickle)

if __name__ == '__main__':
    main()