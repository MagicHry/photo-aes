# -*- coding: utf-8 -*-
"""
模型预测的结果是一个[1,11,1]这样一个三维的数组
我们进而要将其转换为一个分布函数
最后再试图从分布函数中得到最终的得分
"""

import numpy as np
import scipy.stats as stats

def calculateAesScore(rawScore):
    """
    将模型预测出的结果
    转换为真正的美学得分
    :param rawScore:
    :return:
    """
    # 求解均值,标准差
    mean = _mean(rawScore)
    std = _std(rawScore)

    if mean <= 5:
        # 低于4.5分的认为不需要用'乐观'去强化得分
        return mean

    # 概率值推测（核心就是如果一张照片够好，我们去看待它"最好"的一面）
    goodProb = 0
    if mean <= 5.5 and mean > 5:
        goodProb = 0.65

    if mean > 5.5 and mean <= 6.0:
        goodProb = 0.77

    if mean > 6.0:
        goodProb = 0.88

    # 求解对应的高斯分布
    scoreDistribution = stats.norm(loc=mean, scale=std)
    # 求解前20%概率下的得分（为了抹除中庸人士带来的影响）
    score = scoreDistribution.ppf(goodProb)

    return score

def _mean(scores):
    """
    计算分布均值
    :param scores:
    :return:
    """
    si = np.arange(1, 11, 1)
    mean = np.sum(scores * si)
    return mean

def _std(scores):
    """
    计算分布方差
    :param scores:
    :return:
    """
    si = np.arange(1, 11, 1)
    mean = _mean(scores)
    std = np.sqrt(np.sum(((si - mean) ** 2) * scores))
    return std
