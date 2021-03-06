## 数据集基本情况
    
* 文件基本说明
    * 共有102277个训练样本(train_set.csv), 102277个测试样本(test_set.csv)
    * 第0列(id)       ：文章id  
    * 第1列(article)  ：“字”级别上的表示 
    * 第2列(word_seg) ：“词”级别上的表示  
    * 第3列(class)    ： label【类别】
       
* 类别统计
    * 类别样本数统计[共19个类别]
        * 1:5375, 2:2901, 3:8313, 4:3824, 5:2369, 6:6888, 7:3038, 8:6972, 9:7675, 10:4963,
        * 11:3571, 12:5326, 13:7907, 14:6740, 15:7511, 16:3220, 17:3094, 18:7066, 19:5524

    * 训练集 `word_seg`
        * 字典维度有 875129 
        * 平均长度 717, 最大 39759, 最小 6
        
    * 训练集 `article`
        * 字典维度 13516
        * 平均长度 1177, 最大 55804, 最小 50
    
* 变量说明
	* 源数据集的“article”对应sentencen_type=“word”
	* 源数据集的“word_seg”对应的sentence_type=“phrase”
    
## processed_data/数据文件说明
    

* phrase_level_data.csv
    * “phrase”级别的文档表示,分为两列，<label,phrase_doc>  
    * 调用文件../utils/data_util.py中方法 generate_level_data(..)
	    
* word_level_data.csv                        
	* "word"级别上的文档表示，分为两列，<label,word_doc>
	* 调用文件../utils/data_util.py中方法 generate_level_data..)
	
* \*_tw_processed.csv
    * 经过 term weighting 规则处理过滤的结果
    * 调用文件../pre_process/term_weighting_filter.py 中方法 process_data(..)
		
* saved_weight/  各种格式保存的权值文件

  > **\*.pk**  根据weight_type, 将各个词的权重值以字典{“word”：weight}的形式存成pickle文件
  
  > **\*.csv** 根据weight_type, 将各个词的权重值存入csv文件，列名["word", "weight", "count"]
  
  > **\*.json** 根据weight_type, 将权值dict存入json文件, `ju.load(url)`可以直接读取为`dict`
   
    * phrase_level_tf.pk
	    * “phrase”级别上词频文件，格式： dict{word:word_frequence}
	    * 调用文件../term_weighting_model/text_represent.py中方法cal_tf(..)
		
	* phrase_level_bdcValue.pk
		* "phrase"级别上词bdc值，格式： dict{word:bdc_value}
		* 调用文件../term_weighting_model/text_represent.py中方法cal_bdc_value(..)或者方法dc_bdc(..)
		
	* phrase_level_idf.pk
		* "phrase"级别上词的逆文档向量 格式：dict{word:idf_value}
		* 调用文件../term_weighting_model/text_represent.py中方法cal_idf(..)或者方法idf(..)
		
	* phrase_level_tfbdc.pk
		* "phrase"级别上词的tfbdc权重向量，格式: dict{word:tfbdc_value}
		* 调用文件../term_weighting_model/text_represent.py中方法get_tf_bdc_value(..)
		
	* phrase_level_idf.csv
		* "phrase"级别上词的idf值
		* 调用文件../term_weighting_model/text_represent.py中方法idf(..)
		
	* phrase_level_dc.csv
		* "phrase"级别上词的dc值
		* 调用文件../term_weighting_model/text_represent.py中方法dc_bdc(..)
		
	* phrase_level_bdc.csv
		* "phrase"级别上词的bdc值
		* 调用文件../term_weighting_model/text_represent.py中方法dc_bdc(..)
		
	* phrase_level_one_hot.csv
		* "phrase"级别上词的one_hot值
		* 调用文件../term_weighting_model/text_represent.py中方法one_hot(..)
		
	* phrase_level_tf.json
	    * "phrase" 级别上的tf值
	    * 调用文件../term_weighting_model/calc_weightings.py中的方法calc_tf(..)
		
	* phrase_level_dc.json
	    * "phrase" 级别上的dc值
	    * 调用文件../term_weighting_model/calc_weightings.py中的方法calc_dc(..)
		
	* phrase_level_bdc.json
	    * "phrase" 级别上的bdc值
	    * 调用文件../term_weighting_model/calc_weightings.py中的方法calc_bdc(..)
		
* vector/ 存储训练集测试集经过向量化得到的(X, y, X_test)

	* phrase_dc_train.mtx
		* "phrase"级别上以dc值将训练数据集转化成稀疏矩阵
		* 调用文件../term_weighting_model/text_represent.py中方法weihgt_vector(..)
		
* word_distribution/对词的分布统计

	* phrase_level_lf.pk
		* "phrase"级别上词出现的类别频率，格式： dict{word:lf_value}
		* 调用文件../pre_process/data_util.py中方法 calc_labelCount_per_words(..)
		
	* phrase_level_df.pk
		* "phrase"级别上次出现的文档频率，格式: dict{word:df_value}
		* 调用文件../pre_process/data_util.py中方法cal_document_frequency(..)
		
	* phrase_label_count.csv
		* "phrase"级别上词出现在各个类别的文档数
		* 调用文件./pre_process/data_util.py中方法word_in_label(..)
		
* result/ 保存得到的结果文件


## utils 下部分工具方法说明

* `json_util`, 将`dict`类型保存到json文件可以看到数据而且读入方便，个人觉得比pickle更适合保存dict和list类型
```python
from utils.path_util import from_project_root
import utils.json_util as ju
bdc_json_url = from_project_root("processed_data/phrase_level_bdc.json")
bdc_dict = ju.load(bdc_json_url)  # load from json file
ju.dump(bdc_dict, bdc_json_url)  # dump dict object to json file
```

* `data_util`, 提供一些读入和操作数据的公用方法
  * `train_dev_split`, 将csv数据文件8:2划分为固定的训练集和验证集
  * `generate_level_data`, 生成`processed_data/phrase_level_data.csv`和`processed_data/word_level_data.csv`，可选是否包括`header`


## Git使用说明
* 登录 Github 添加自己公钥到 Github 账号
  * `git-bash` 运行 `cat ~/.ssh/id_rsa.pub`，复制结果在[此处](https://github.com/settings/keys)选择`New SSH key`粘贴到`Key`输入框，提示文件不存在则先运行`ssh-keygen`一直点回车就行
  
* clone 项目
  * 在保存项目的位置 `git-bash` 运行 `git clone git@github.com:csJd/dg_text.git`，生成的 `dg_text` 为项目文件夹
  
* push 更改
  * 将代码复制到 `dg_text` 文件夹恰当位置，运行以下命令push更改，以后直接在dg_text文件夹下开发，后续修改了项目文件也是这样push更改：
```sh
git add .
git commit -m "message"
git pull
git push
```
  * 对git不熟悉可以使用Pycharm快捷键`Ctrl + T` pull， 然后`Ctrl + K` push

* pull 更改
  * pull 其他人对项目文件作更改, 运行 `git pull` 即可
  
* 使用git尽量不要修改别人写的代码，而是调用其中的方法
   

## Pycharm 建议设置

* 换行符统一为'\n'
  * File | Settings | Editor | Code Style
    * `Line separator` 选择 `Unix and OS X (\n)`

* 编码统一为`UTF-8`
  * File | Settings | Editor | File Encodings
    * Global 和 Project 都选择 `UTF-8`
    * 下方 Default encoding for properties files也选择 `UTF-8`

* Python Doc 使用 Google 风格
  * File | Settings | Tools | Python Integrated Tools
    * `Docstring format` 选择 `Google`

* 设置Python 默认代码
  * File | Settings | Editor | File and Code Templates
    * 选择 `Python Script` 粘贴以下内容, `${USER}`可换为自己想显示的昵称
    * 可以自己按需修改

```python
# encoding: utf-8
# created by ${USER} on ${DATE}


def main():
    pass


if __name__ == '__main__':
    main()

```

* Python代码中的文件路径
  * 建议所有路径都使用 `utils` 包下的 `path_util.from_project_root` 方法得到绝对路径
  * 例如要访问`data/train_set.csv`时，先鼠标右键复制`train_set.csv`的相对路径，然后直接调用方法就好
```python
from utils.path_util import from_project_root
train_data_url = from_project_root('data/train_set.csv')
print(train_data_url)
```

           
