# -*- coding: utf-8 -*-
"""
利用socket通信
向美学微服务请求进行美学计算
"""

import socket
import os.path
from core.helper import LogUtils as log
from core.helper import FileUtils

# TODO:其实这边需要和微服务的配置进行统一，这样图方便了
LISTEN_IP = '127.0.0.1'
LISTEN_PORT = 8848
CODE_ERROR = '500'
CODE_OK = '200'
CODE_FILE_ERROR = '400'
END_MARKER = '!EOF!'


def make_request(abs_img_path):
    """
    使用Socket进行图片美学打分
    真正的模型预测在美学微服务中
    :param abs_img_path:
    :return:
    """
    # 进行文件检查
    suc, normed_path, msg = FileUtils.valid_path(abs_img_path, relative_path=False)
    if not suc:
        log.error('Invalid File path : %s' % abs_img_path)
        return 'Invalid File'
    abs_img_path = normed_path

    try:
        # 使用ipV4
        socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接
        socket_conn.connect((LISTEN_IP, LISTEN_PORT))
        rtn_code = (socket_conn.recv(2048)).decode('utf-8')
        if rtn_code == CODE_ERROR:
            log.error('Aes model not init')
            return 'Model Init Error'
        elif rtn_code == CODE_OK:
            log.info('Socket established!')

            # 添加END_MAKRER给微服务进行内容识别
            test_img_path = abs_img_path
            test_img_path += END_MARKER
            log.info('Send info -> %s' % test_img_path)

            # 发送请求
            socket_conn.send(test_img_path)
            aes_score = (socket_conn.recv(2048)).decode('utf-8')

            log.info('The aes score is %s' % aes_score)
            socket_conn.close()

            return aes_score
        else:
            socket_conn.close()
            return 'Unknow Error'
    finally:
        if socket_conn:
            socket_conn.close()