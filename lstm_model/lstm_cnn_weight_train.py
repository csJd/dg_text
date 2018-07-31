#coding=utf-8

import tensorflow as tf
import time
import os
from lstm_model.lstm_cnn_weight_model import LSTM_CNN_Model as LSTM_CNN_Model
import numpy as np
import Data_helper
from utils.path_util import from_project_root
from tensorflow.contrib import learn
import pickle as pk
import collections
from sklearn.metrics import f1_score


#Data loading params
tf.flags.DEFINE_integer("num_classes",19,"number of classes")
tf.flags.DEFINE_integer("embedding_size",64,"Dimensionality of word embedding")
tf.flags.DEFINE_integer("hidden_size",64,"Dimensionality of GRU hidden layer(default 50)") #===============
tf.flags.DEFINE_float("dev_sample_percentage",0.002,"dev_sample_percentage")
tf.flags.DEFINE_integer("batch_size",100,"Batch Size of training data(default 50)")
tf.flags.DEFINE_integer("checkpoint_every",100,"Save model after this many steps (default 100)")
tf.flags.DEFINE_integer("num_checkpoints",10,"Number of checkpoints to store (default 5)")
tf.flags.DEFINE_integer("evaluate_every",50,"evaluate every this many batches")
tf.flags.DEFINE_float("learning_rate",0.01,"learning rate")  #====================
tf.flags.DEFINE_integer("grad_clip",5,"grad clip to prevent gradient explode")
tf.flags.DEFINE_integer("epoch",3,"number of epoch")
tf.flags.DEFINE_integer("max_word_in_sent",1000,"max_word_in_sent")
tf.flags.DEFINE_float("regularization_rate",0.001,"regularization rate random") #=======================

# cnn
tf.flags.DEFINE_string("filter_sizes","2,3,4","the size of the filter")
tf.flags.DEFINE_integer("num_filters",64,"the num of channels in per filter")

tf.flags.DEFINE_float("rnn_input_keep_prob",0.9,"rnn_input_keep_prob")
tf.flags.DEFINE_float("rnn_output_keep_prob",0.9,"rnn_output_keep_prob")

tf.flags.DEFINE_string("train_file","lstm_model/processed_data/filter_phrase_level_data_train.csv","train file url")
tf.flags.DEFINE_string("vocab_file","lstm_model/processed_data/phrase_level_vocab.pk","vocab file url")
tf.flags.DEFINE_string("dc_file","lstm_model/processed_data/phrase_level_dc.pk","dc file url")

FLAGS = tf.flags.FLAGS

# =====================load data========================================================================================
# load the training data
# 准备数据
# x_text : 分好词的字符串数组 , example: ["a b c","d e f g h"]
# y : label example: [[0,1],[1,0],...]

print("Loading Data...")
x_text,y = Data_helper.load_data_and_labels(from_project_root(FLAGS.train_file))
# =====================end load data =======================================================================================

# =====================build vocab =====================================================================================
vocab_dict = pk.load(open(from_project_root(FLAGS.vocab_file),'rb'))
x_vecs = []
for x in x_text:
    x_word_list = x.strip().split()
    x_vec = [0]*FLAGS.max_word_in_sent
    for i in range(min(FLAGS.max_word_in_sent,len(x_word_list))):
        x_vec[i] = vocab_dict[x_word_list[i]]
    x_vecs.append(x_vec)
# =====================build vocab =====================================================================================
# =====================create term weight ==============================================================================
dc_dict = pk.load(open(from_project_root(FLAGS.dc_file), 'rb'))
term_weights = []
for x in x_text:
    x_word_list = x.strip().split()
    sen_length = len(x_word_list)
    # 计算文档级别的tf
    tf_dict = collections.defaultdict(int)
    for word in x_word_list:
        tf_dict[word] += 1
    term_weight = [0] * FLAGS.max_word_in_sent
    for i in range(min(FLAGS.max_word_in_sent,len(x_word_list))):
        term_weight[i] = tf_dict[x_word_list[i]] / sen_length * dc_dict[x_word_list[i]]

    term_weights.append(term_weight)

print("加载数据完成.....")
# =====================create term weight ==============================================================================

# =====================split dev and text ==============================================================================

# 数据集划分

dev_sample_index = -1 * int( FLAGS.dev_sample_percentage * len(y))

x_train,x_dev = x_vecs[:dev_sample_index],x_vecs[dev_sample_index:]
y_train,y_dev = y[:dev_sample_index],y[dev_sample_index:]
term_weight_trian,term_weight_dev = term_weights[:dev_sample_index],term_weights[dev_sample_index:]

# 清除内存
del x,y

# 格式化输出
print("Train / Dev split: {:d} / {:d}".format(len(y_train),len(y_dev)))

# =====================split dev and text ==============================================================================


# load embedding mat
embedding_mat = tf.Variable(tf.truncated_normal((len(vocab_dict)+1,FLAGS.embedding_size)))

print("data load finished!!!")

'''
vocab_size,num_classes,embedding_size=300,hidden_size=50
'''

with tf.Session() as sess:
    new_model = LSTM_CNN_Model(
        num_classes=FLAGS.num_classes,
        embedding_size = FLAGS.embedding_size,
        hidden_size = FLAGS.hidden_size,
        init_embedding_mat = embedding_mat,
        max_doc_length = FLAGS.max_word_in_sent,
        filter_sizes = list(map(int, FLAGS.filter_sizes.split(","))),
        num_filters = FLAGS.num_filters
    )

    with tf.name_scope("loss"):

        # 给GRU加上L2正则化
        tv = tf.trainable_variables()  # 得到所有可以训练的参数，即所有trainable=True的tf.Variable / tf.get_variable
        regularization_cost = FLAGS.regularization_rate * tf.reduce_sum([tf.nn.l2_loss(v) for v in tv]) #0.001是一个lambda超参数

        original_cost = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits(labels=new_model.input_y,
                                                                     logits=new_model.out))

        loss = original_cost + regularization_cost

        # loss =  -tf.reduce_sum(new_model.input_y*tf.log(tf.clip_by_value(new_model.out,1e-10,1.0)))

    with tf.name_scope("accuray") :
        predict = tf.argmax(new_model.out,axis=1,name="predict")
        label = tf.argmax(new_model.input_y,axis=1,name="label")
        acc = tf.reduce_mean(tf.cast(tf.equal(predict,label),tf.float32))

    # create model path
    timestamp = str( int(time.time()))
    out_dir = os.path.abspath(os.path.join(os.path.curdir,"runs",timestamp))
    print("Wrinting to {} \n".format(out_dir))

    # global step
    global_step = tf.Variable(0,trainable=False)
    optimizer = tf.train.AdamOptimizer(FLAGS.learning_rate)

    # RNN中常用的梯度截断，防止出现梯度过大难以求导的现象
    tvars = tf.trainable_variables()
    grads, _ = tf.clip_by_global_norm(tf.gradients(loss, tvars), FLAGS.grad_clip)
    grads_and_vars = tuple(zip(grads, tvars))
    train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

    # Keep track of gradient values and sparsity(optional)
    # Keep track of gradient values and sparsity (optional)
    grad_summaries = []
    for g, v in grads_and_vars:
        if g is not None:
            grad_hist_summary = tf.summary.histogram("{}/grad/hist".format(v.name), g)
            grad_summaries.append(grad_hist_summary)

    grad_summaries_merged = tf.summary.merge(grad_summaries)

    loss_summary = tf.summary.scalar('loss',loss)
    acc_summary = tf.summary.scalar('acc',acc)

    train_summary_op = tf.summary.merge([loss_summary,acc_summary,grad_summaries_merged])
    train_summary_dir = os.path.join(out_dir,"summaries","train")
    train_summary_writer = tf.summary.FileWriter(train_summary_dir,sess.graph)

    dev_summary_op = tf.summary.merge([loss_summary, acc_summary])
    dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
    dev_summary_writer = tf.summary.FileWriter(dev_summary_dir, sess.graph)

    checkpoint_dir = os.path.abspath(os.path.join(out_dir,"checkpoints"))
    checkpoint_prefix = os.path.join(checkpoint_dir,"model")
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)
    saver = tf.train.Saver(tf.global_variables(),max_to_keep=FLAGS.num_checkpoints)

    sess.run(tf.global_variables_initializer())

    def train_step(x_batch,y_batch,term_weight_bath):

        feed_dict={
            new_model.input_x:x_batch,
            new_model.input_y:y_batch,
            new_model.term_weight:term_weight_bath,
            new_model.rnn_input_keep_prob:FLAGS.rnn_input_keep_prob,
            new_model.rnn_output_keep_prob:FLAGS.rnn_output_keep_prob
        }
        _,step,summaries,cost,accuracy = sess.run([train_op,global_step,train_summary_op,loss,acc],feed_dict)

        time_str = str( int(time.time()))
        print("{} : step {}, loss {:g} , acc {:g}".format(time_str,step,cost,accuracy))

        return step

    def dev_step(x_batch,y_batch,term_weight_batch,writer=None):

        feed_dict={
            new_model.input_x:x_batch,
            new_model.input_y:y_batch,
            new_model.term_weight:term_weight_batch,
            new_model.rnn_input_keep_prob: 1.0,
            new_model.rnn_output_keep_prob: 1.0
        }

        step, summaries, cost, accuracy,input_y,predict_y = sess.run([global_step, dev_summary_op,
                                                                      loss, acc,new_model.input_y,new_model.predict], feed_dict)
        print(input_y)
        print(predict_y)

        time_str = str(int(time.time()))
        print("++++++++++++++++++dev++++++++++++++{}: step {}, loss {:g}, acc {:g}".format(time_str, step, cost,
                                                                                           accuracy))

        if writer:
            writer.add_summary(summaries, step)

    for epoch in range(FLAGS.epoch):
        print('current epoch %s' % (epoch + 1))

        for i in range(0,len(y_train)-FLAGS.batch_size,FLAGS.batch_size):

            x_batch = x_train[i:i+FLAGS.batch_size]
            y_batch = y_train[i:i+FLAGS.batch_size]
            term_weight_batch = term_weight_trian[i:i+FLAGS.batch_size]
            step = train_step(x_batch,y_batch,term_weight_batch)

            if step % FLAGS.evaluate_every == 0:
                dev_step(x_dev,y_dev,term_weight_dev,dev_summary_writer)

            if step % FLAGS.checkpoint_every == 0 :
                path = saver.save(sess,checkpoint_prefix,global_step=step)
                print("Saved model checkpoint to {} \n".format(path))