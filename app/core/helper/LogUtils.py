# coding=utf-8
import logging
import os
"""
Flask-Logger
简易的封装与配置
"""

flaskApp = None

def register_logger(app):
    """
    注册本地输出日志
    :return:
    """
    global flaskApp
    flaskApp = app
    log_file_name = os.path.join(flaskApp.config['LOG_FOLDER'], 'log.txt')
    logging.basicConfig(filename=log_file_name,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def error(msg):
    global flaskApp
    flaskApp.logger.error(msg)

def info(msg):
    global flaskApp
    flaskApp.logger.info(msg)



