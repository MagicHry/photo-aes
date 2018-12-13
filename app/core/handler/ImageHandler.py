# -*- coding: utf-8 -*-
import simplejson
import PIL
from PIL import Image
import traceback
from werkzeug import secure_filename
import os
from core.model.upload_file import uploadfile
from config import ServerConfig
import core.helper.FileUtils as fileutils
"""
图片上传
图片下载
处理函数
"""

def handlePhotoPost(files, app, userId):
    """
    处理图片上传请求：
    1.处理表单数据
    2.数据校验
    3.数据存储，返回结果
    MARK:这边的处理，到照片数据存储完毕即可，后续的操作还是在对应的路由函数中进行
    :param files:
    :param app:
    :return:
    """
    filename = secure_filename(files.filename)
    filename = gen_file_name(filename, app)
    mime_type = files.content_type

    # 文件名不符合直接没了
    if not allowed_file(files.filename):
        result = uploadfile(name=filename, type=mime_type, size=0, not_allowed_msg=u"不支持的文件类型~"), None

    else:
        # 每个用户拥有自己的缓存目录
        suc, userImgFolder, userThumbFolder = setup_user_cache(userId, app)
        if suc:
            uploaded_file_path = os.path.join(userImgFolder, filename)
            # 保存原图
            files.save(uploaded_file_path)

            # 保存缓存图片
            if mime_type.startswith('image'):
                create_thumbnail(filename, userImgFolder, userThumbFolder)

            # 计算图片大小
            size = os.path.getsize(uploaded_file_path)

            # 存储完成
            result = uploadfile(name=filename, type=mime_type, size=size), uploaded_file_path
        else:
            result = uploadfile(name=filename, type=mime_type, size=0, not_allowed_msg=u"文件存储有误"), None

    return result

def handlePhotoGet(app, aes_score_container, user_id):
    """
    处理图片上传成功后，对于图片数据的GET请求
    MARK：和直接获取大图资源的请求是不一样的
    :param files:
    :param app:
    :return:
    """

    file_display = []
    # 先拿到对应的图片缓存目录
    suc, userImgFolder, _ = setup_user_cache(user_id, app)
    if not suc:
        return file_display

    # 拿到图片缓存目录下对应的有效图片
    files = [f for f in os.listdir(userImgFolder) if
             os.path.isfile(os.path.join(userImgFolder, f)) and f not in ServerConfig.IGNORED_FILES]

    for f in files:
        size = os.path.getsize(os.path.join(userImgFolder, f))
        file_saved = uploadfile(name=f, size=size)
        if f in aes_score_container:
            aes_score = aes_score_container[f]
            file_saved.aes_score = aes_score
        else:
            file_saved.aes_score = u'未知错误'

        file_display.append(file_saved.get_file())

    return file_display

def allowed_file(filename):
    """
    校验图片格式
    :param filename:
    :return:
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ServerConfig.ALLOWED_EXTENSIONS


def gen_file_name(filename, app):
    """
    根据上传文件名，生成一个存在后端的文件名
    这里这么做是涉及到文件名转码的问题
    """

    i = 1
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        name, extension = os.path.splitext(filename)
        filename = '%s_%s%s' % (name, str(i), extension)
        i += 1

    return filename

def setup_user_cache(userId, app):
    """
    此函数帮助构建用户缓存目录，和用户缩略图缓存目录
    :param userId:
    :return:
    """
    uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], userId)
    if fileutils.setup_folder(app.config['UPLOAD_FOLDER'], userId):
        uploaded_file_thumb_path = os.path.join(uploaded_file_path, app.config['THUMBNAIL_FOLDER_NAME'])
        if fileutils.setup_folder(uploaded_file_path, app.config['THUMBNAIL_FOLDER_NAME']):
            return True, uploaded_file_path, uploaded_file_thumb_path
    return False, None, None


def create_thumbnail(image, imgFolder, thumbFolder):
    """
    对于上传的大图
    生成一个缩略图进行存储
    前端后续会使用到
    :param image:
    :param app:
    :return:
    """
    try:
        base_width = 80
        img = Image.open(os.path.join(imgFolder, image))
        if img:
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)
            thumb_path = os.path.join(thumbFolder, image)
            img.save(thumb_path)
            return True

        return False

    except:
        print traceback.format_exc()
        return False