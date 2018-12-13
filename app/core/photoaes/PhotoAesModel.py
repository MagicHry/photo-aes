# coding=utf-8
"""
模型管理
负责启动tensorflow，运行美学程序使用的模型
模型本身为Inception-V2模型
"""
import numpy as np
from keras.models import Model
from keras.layers import Dense, Dropout
from keras.applications.inception_resnet_v2 import InceptionResNetV2
from keras.applications.inception_resnet_v2 import preprocess_input
from keras.preprocessing.image import load_img, img_to_array
import tensorflow as tf
from core.helper import LogUtils as log
import Scoring as score
import os

# 模型
model = None
# 模型初始化flag
hasModelInit = False
# 全局graph
graph = None

def initFinish():
    """
    是否初始化完毕
    :return:
    """
    global  model, hasModelInit, graph
    if model == None or (not hasModelInit) or graph == None:
        return False
    return True

def initModel(weightsFilePath):
    """
    模型初始化
    全局只会初始化一次
    包括：
    1.inceptionV2结构化定义
    2.加载模型权重
    :param weightsFilePath:
    :return:
    """
    # 初始化过，就不要再初始化了
    global model, hasModelInit, graph
    if model != None and hasModelInit:
        log.info('the model has already init before, now re-use it')
        return

    # 模型构建
    log.info(('start to build model based on weights in -> %s' % (weightsFilePath)))
    with tf.device('/CPU:0'):
        # 模型参数定义
        base_model = InceptionResNetV2(input_shape=(None, None, 3), include_top=False, pooling='avg', weights=None)
        x = Dropout(0.75)(base_model.output)
        x = Dense(10, activation='softmax')(x)
        model = Model(base_model.input, x)
        # 读取权重数据
        model.load_weights(weightsFilePath)

    graph = tf.get_default_graph()
    hasModelInit = True
    log.info('model init complete!')
    return

def runModelForSingleImg(imgFilePath, resize):
    """
    运行模式 - 单照片运行
    这个函数必须在模型已经初始化完毕之后才能使用
    :param imgFilePathLst:
    :param resize:
    :return:
    :param imgFilePath:
    :param resize:
    :return:
    """
    global model, hasModelInit, graph
    if model == None or (not hasModelInit):
        log.error('Failed to calculate aes score : model is not initialized!')
        return

    with tf.device('/CPU:0'):
        with graph.as_default():

            log.info('Now processing img -> %s' % (imgFilePath))
            # 预处理
            imgArr = _preImgProcess(imgFilePath, resize)
            # 预测
            scores = model.predict(imgArr, batch_size=1, verbose=0)[0]
            aesScore = score.calculateAesScore(scores)
            aesScore = aesScore * 10
            return aesScore

def runModel(imgFilePathLst, resize):
    """
    运行模式 - 多照片运行
    这个函数必须在模型已经初始化完毕之后才能使用
    :param imgFilePathLst:
    :param resize:
    :return:
    """
    global model, hasModelInit
    if model == None or (not hasModelInit):
        log.error('Failed to calculate aes score : model is not initialized!')
        return

    with tf.device('/CPU:0'):
        scoreLst = []
        for imgPath in imgFilePathLst:
            log.info('Now processing img -> %s' % (imgPath))
            # 预处理
            imgArr = _preImgProcess(imgPath, resize)
            # 预测
            scores = model.predict(imgArr, batch_size=1, verbose=0)[0]
            aesScore = score.calculateAesScore(scores)
            aesScore = aesScore * 10
            # log.success('The aes score for img -> %s is %0.3f' % (imgPath, aesScore))
            _, imgName = os.path.split(imgPath)
            scoreLst.append((imgName, aesScore))

        # 进行排序
        sortedScoreLst = sorted(scoreLst, key=lambda s: s[1], reverse=True)
        return sortedScoreLst


def _preImgProcess(imgPath, resize):
    """
    图片预处理
    在输入模型前，需要对图片进行一些简单的预处理
    包括：
    1.一维化
    2.resize
    :param resize:
    :return:
    """
    destSize = None
    if resize:
        destSize = (224, 224)
    img = load_img(imgPath, target_size=destSize)
    imgArr = img_to_array(img)
    imgArr = np.expand_dims(imgArr, axis=0)
    imgArr = preprocess_input(imgArr)
    return imgArr