# coding: utf-8
# created by deng on 7/27/2018

from xgboost.sklearn import XGBClassifier
from lightgbm.sklearn import LGBMClassifier
from sklearn.svm import SVC, LinearSVC
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.linear_model import SGDClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib
from sklearn.metrics import f1_score, accuracy_score
from time import time
import numpy as np
import scipy.sparse as sp
import pandas as pd

from utils.path_util import from_project_root
from utils.proba_util import predict_proba
from term_weighting_model.transformer import generate_vectors
from term_weighting_model.stacker import generate_meta_feature, gen_data_for_stacking
from term_weighting_model.stacker import model_stacking_from_pk

N_JOBS = 1
N_CLASSES = 19
RANDOM_STATE = 10
CV = 5


def init_param_grid(clf=None, clf_type=None):
    """

    Args:
        clf: classifier
        clf_type: str of classifier type, not required if clf is not None

    Returns:
        param_grid for clf

    """
    if isinstance(clf, SVC) or clf_type == 'svc':
        param_grid = [
            {'C': [1, 10, 100, 1000], 'kernel': ['linear']},
            {'C': [1, 10, 100, 1000], 'gamma': [0.01, 0.001], 'kernel': ['rbf']},
        ]
    elif isinstance(clf, LGBMClassifier) or clf_type == 'lgbm':
        param_grid = [
            # {'boosting_type': ['gbdt', 'dart', 'rf'], 'learning_rate': [0.1, 0.01]}
            {'boosting_type': ['gbdt'], 'learning_rate': [0.1]},
        ]
    elif isinstance(clf, XGBClassifier) or clf_type == 'xgb':
        param_grid = [
            # {'learning_rate': [0.3, 0.1, 0.01]}
            {'learning_rate': [0.1]}
        ]
    elif isinstance(clf, LinearSVC) or clf_type == 'lsvc':
        param_grid = [
            # {'C': [0.5, 1, 10]}
            {'C': [1]}
        ]
    else:
        param_grid = None
    return param_grid


def init_linear_clfs():
    """ init linear classifiers for training

    Returns:
        dict, clfs

    """
    clfs = dict()

    # add linearSVC model
    clfs['lsvc'] = LinearSVC()

    # add SGD model
    # clfs['sgd'] = SGDClassifier()

    # add KNN model
    # clfs['knn'] = KNeighborsClassifier()

    return clfs


def init_clfs():
    """ init classifiers to train
    
    Returns:
        dict, clfs

    """
    clfs = dict()

    # Add xgb model
    clfs['xgb'] = XGBClassifier(n_jobs=-1)

    # Add lgbm model
    # clfs['lgbm'] = LGBMClassifier()

    # Add svc model
    # clfs['svc'] = SVC()

    return clfs


def tune_clf(clf, X, y, param_grid):
    """

    Args:
        clf: clf to be tuned
        param_grid: param_grid for GridSearchCV
        X: X for fit
        y: y for fit

    Returns:
        GridSearchCV: fitted clf

    """
    if param_grid is None:
        print("None as param_grid is invalid, the original clf will be returned")
        return clf
    s_time = time()
    clf = GridSearchCV(clf, param_grid, scoring='f1_macro', n_jobs=N_JOBS, cv=CV,
                       error_score=0, verbose=True)
    clf.fit(X, y)
    e_time = time()
    # print cv results
    print("grid_search_cv is done in %.3f seconds" % (e_time - s_time))
    for i in range(CV):
        col = 'split{}_test_score'.format(i)
        print(col, '=', clf.cv_results_[col])
    print("mean_macro_f1 =", clf.cv_results_['mean_test_score'])
    return clf


def train_clfs(clfs, X, y, test_size=0.2, tuning=False, random_state=None):
    """ train clfs

    Args:
        clfs: classifiers
        X: data X of shape (samples_num, feature_num)
        y: target y of shape (samples_num,)
        test_size: test_size for train_test_split
        tuning: whether to tune parameters use param_grid_cv
        random_state: random_state for train_test_split

    """

    # split data into train and test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y)
    print("train data shape", X_train.shape, y_train.shape)
    print("dev data shape  ", X_test.shape, y_test.shape)
    for clf_name in clfs:
        clf = clfs[clf_name]
        if tuning:
            print("grid search cv on %s is running" % clf_name)
            param_grid = init_param_grid(clf)
            clf = tune_clf(clf, X, y, param_grid)
            # print('cv_results\n', clf.cv_results_)
            clf = clf.best_estimator_

        print("%s model is training" % clf_name)
        if not tuning:
            s_time = time()
            clf.fit(X_train, y_train)
            e_time = time()
            print(" training finished in %.3f seconds" % (e_time - s_time))

        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        macro_f1 = f1_score(y_test, y_pred, average='macro')
        print(" accuracy = %f\n f1_score = %f\n" % (acc, macro_f1))

    return clfs


def train_and_gen_result(clf, X, y, X_test, use_proba=False, save_url=None, n_splits=1, random_state=None):
    """ train and generate result with specific clf

    Args:
        clf: classifier
        X: vectorized data
        y: target
        X_test: test data
        use_proba: predict probabilities of labels instead of label
        save_url: url to save the result file
        n_splits: n_splits for K-fold, None to not use k-fold
        random_state: random_state for 5-fold

    """
    if n_splits > 1:
        slf = StratifiedKFold(n_splits=n_splits, shuffle=bool(random_state), random_state=random_state)
        y_pred_proba = np.zeros((X_test.shape[0], N_CLASSES))
        for train_index, cv_index in slf.split(X, y):
            X_train = X[train_index]
            y_train = y[train_index]
            clf.fit(X_train, y_train)
            y_pred_proba += predict_proba(clf, X_test, X_train, y_train)
        y_pred_proba /= n_splits
        y_pred = y_pred_proba.argmax(axis=1) + 1

    else:
        clf.fit(X, y)
        y_pred_proba = predict_proba(clf, X_test, X, y)
        y_pred = clf.predict(X_test)

    if use_proba:
        result_df = pd.DataFrame(y_pred_proba, columns=['class_prob_' + str(i + 1) for i in range(N_CLASSES)])
    else:
        result_df = pd.DataFrame(y_pred, columns=['class'])
    if save_url:
        result_df.to_csv(save_url, index_label='id')
    return result_df


def main():
    clfs = init_clfs()
    # clfs = init_linear_clfs()

    # load from pickle
    # pk_url = from_project_root("processed_data/vector/stacked_proba_XyX_test_50.pk")
    # print("loading data from", pk_url)
    # X, y, X_test = joblib.load(pk_url)

    # load from stacking
    pk_urls = [
        from_project_root("processed_data/vector/deng_34_xgb_0.787.pk"),
        from_project_root("processed_data/vector/deng_28_idf_xgb_0.782.pk"),
        from_project_root("processed_data/vector/deng_50_bdc_xgb_0.786.pk"),
        from_project_root("processed_data/vector/xingwei_rcnn_0.7897.pk"),
        from_project_root("processed_data/vector/xingwei_lstm_0.788.pk"),
        from_project_root("processed_data/vector/xingwei_rcnn_0.79242.pk"),
        from_project_root("processed_data/vector/xingwei_lstm_0.79.pk"),
        from_project_root("processed_data/vector/xhz_baseline_0.76.pkl"),
        from_project_root("processed_data/vector/xhz_baseline_max_0.71.pkl"),
        from_project_root("processed_data/vector/xhz_cnn_0.77.pkl"),
        from_project_root("processed_data/vector/peng_han_0.767.pk"),
        from_project_root("processed_data/vector/zt_fasttext_400.pk"),
        from_project_root("processed_data/vector/ft_300_0.72.pk"),
    ]
    X, y, X_test = model_stacking_from_pk(pk_urls)

    train_url = from_project_root("data/train_set.csv")
    test_url = from_project_root("data/test_set.csv")

    # generate from original csv
    # X, y, X_test = generate_vectors(train_url, test_url, column='word_seg', max_n=3, min_df=3, max_df=0.8,
    #                                 max_features=2000000, balanced=False, re_weight=9)
    # X = sp.hstack([X, X_a])  # append horizontally on sparse matrix

    # generate meta features
    # X = np.append(X, generate_meta_feature(train_url), axis=1)
    # X_test = np.append(X_test, generate_meta_feature(test_url), axis=1)

    print(X.shape, y.shape, X_test.shape)
    train_clfs(clfs, X, y, tuning=True, random_state=RANDOM_STATE)

    # clf = LinearSVC(C=1)
    clf = XGBClassifier(n_jobs=-1)  # xgb's default n_jobs=1
    # clf = LGBMClassifier()

    use_proba = False
    n_splits = 1
    save_url = from_project_root("processed_data/com_result/{}_stk_xgb_{}_{}_fold.csv"
                                 .format(X.shape[1] // N_CLASSES, 'proba' if use_proba else 'label', n_splits))
    train_and_gen_result(clf, X, y, X_test, use_proba=use_proba, save_url=save_url,
                         n_splits=n_splits, random_state=RANDOM_STATE)

    # save_url = from_project_root("processed_data/vector/{}_aug_dc_xgb.pk".format(X.shape[1] // N_CLASSES))
    # joblib.dump(gen_data_for_stacking(clf, X, y, X_test, n_splits=5, random_state=None), save_url)

    pass


if __name__ == '__main__':
    main()
