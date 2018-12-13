# -*- coding: utf-8 -*-
"""
文件处理模块
"""
import os


def valid_path(path, relative_path=True):
    """
    校验输入路径是否合法，包括｛文件夹，文件｝
    目前只支持绝对路径
    :param path: 输入路径
    :return: is_valid:是否合法；norm_path:在合法的前提下，会返回统一化过的路径; error_msg:在不合法的前提下，返回错误信息
    """
    error_msg = ""
    #判空
    if path == None or path == '':
        error_msg = "empty input path"
        return (False,path,error_msg)

    #统一化
    norm_path = __norm_path_str__(path)

    #是否为绝对路径
    if not os.path.isabs(norm_path) and (not relative_path):
        error_msg = "input path is not abs path"
        return (False, path, error_msg)

    #判断路径是否真的存在
    if not os.path.exists(norm_path):
        error_msg = "input path is not exist"
        return (False, path, error_msg)

    return (True,norm_path,error_msg)


def setup_folder(parent_path,folder_name,relative_path=True):
    """
    文件夹check，确保两件事情:{如果文件夹缺失，那么进行创建，如果文件夹存在，返回True}
    :param root_path: 上一级目录名称，要求必须是文件夹
    :param folder_name: 待确认文件夹名称
    :return:是否成功确认待确认文件夹
    """
    # 校验
    is_legal,normed_parent_path,error_msg = valid_path(parent_path)
    if not is_legal:
        return False

    if not os.path.isdir(normed_parent_path):
        # 要求必须为文件夹
        return False

    # 只检查第一层级
    child_folders = os.listdir(normed_parent_path)
    if child_folders != None or len(child_folders) != 0:
        for cur_folder in child_folders:
            if cur_folder == folder_name:
                return True
        # 直接创建
        return __create_folder__(normed_parent_path, folder_name)
    else:
        # 直接创建
        return __create_folder__(normed_parent_path,folder_name)



def clear_folder(folder_path):
    """
    清空指定文件夹下面的文件()
    :param folder_path: 文件夹路径
    :return: clear_suc:是否清空成功；err_msg：清空失败的情况下，返回错误原因
    """
    is_valid,normed_folder_path,err_msg = valid_path(folder_path)
    if not is_valid:
        return (False,err_msg)

    if not os.path.isdir(normed_folder_path):
        return (False,"The input folder path %s is not a folder" % normed_folder_path)

    files = os.listdir(normed_folder_path)
    try:
        for file in files:
            file_path = __norm_path_str__(os.path.join(normed_folder_path,file))
            os.remove(file_path)
        return (True,"")
    except:
        return (False, "Failed to remove files under folder path %s" % normed_folder_path)


def __create_folder__(parent_path,folder_name):
    """
    实际上是{setup_folder}的子函数
    不做任何检查，直接创建文件夹
    :param parent_path:上级目录
    :param folder_name:文件夹名称
    :return:是否成功创建
    """
    folder_abs_path = os.path.join(parent_path, folder_name)
    folder_abs_path = __norm_path_str__(folder_abs_path)
    try:
        os.mkdir(folder_abs_path)
        return True
    except:
        return False

def __norm_path_str__(input_path):
    """
    考虑到跨平台的原因，这边做一下路径同一化，保证在大部分OS上面都是可以用的
    目前不支持输入带有Symbolic link的路径
    :param input_path: 输入路径，由于操作系统的原因，可能是各种各样的
    :return: 统一化后的路径
    """

    #路径统一化
    input_path = os.path.normpath(input_path)
    #Case统一化
    input_path = os.path.normcase(input_path)

    return input_path;