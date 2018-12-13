# -*- coding: utf-8 -*-
# !flask/bin/python
import os
import json as simplejson
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session, escape
from flask_bootstrap import Bootstrap
import core.handler.ImageHandler as ImgHandle
import core.handler.LoginHandler as UsrHandle
from config import ServerConfig
from flask_sqlalchemy import SQLAlchemy
import random
from core.helper import FileUtils
from core.helper import LogUtils as log
from core.photoaes import PhotoAesModel as AesModel

# flask 后台相关
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gaokuaidian'
app.config['UPLOAD_FOLDER'] = 'data/'
app.config['LOG_FOLDER'] = 'logs/'
app.config['THUMBNAIL_FOLDER_NAME'] = 'thumbnail'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/aesinfo.db'
app.config['AES_MODEL_PATH'] = 'weights/weights.h5'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
log.register_logger(app)
app.logger.name="PhotoAes"

# 数据库初始化
db.create_all()

# 照片美学相关环境启动
AesModel.initModel(app.config['AES_MODEL_PATH'])

"""
db对象，这里因为只是用来存储一下文件名，用户id和照片美学得分的
所以简单做，只是一个简单存储而已
"""
class AesUserInfo(db.Model):

    __tablename__ = 'TABLE_AESUSER'
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.String(120), unique=False)
    photoName = db.Column(db.String(120), unique=False)
    photoScore = db.Column(db.String(120), unique=False)

    def __init__(self, userId, photoName, photoScore):
        self.userId = userId
        self.photoName = photoName
        self.photoScore = photoScore

    def __repr__(self):
        return '<User %r>' % self.username

def addAesInfo(user_id, file_name, aes_score, db):
    """
    向DB增加一条美学数据
    这里的检查交给调用者去做
    :param user_id:
    :param file_name:
    :param db:
    :return:
    """
    user_aes_info = AesUserInfo(user_id, file_name, aes_score)
    db.session.add(user_aes_info)
    db.session.commit()
    log.info('Add aes info into db for img -> %s' % file_name)


def queryAesInfoById(user_id):
    """
    通过user_id
    查询对应用户已经进行过美学评测的所有照片
    :param user_id:
    :param db:
    :return:
    """
    aes_score_container = {}
    aes_info_lst = AesUserInfo.query.filter_by(userId=user_id)

    if aes_info_lst is None:
        return aes_score_container

    for aesInfo in aes_info_lst:
        aes_score_container[aesInfo.photoName] = aesInfo.photoScore
        log.info('The aes score for img=%s is %s' % (aesInfo.photoName, aesInfo.photoScore))

    return aes_score_container

def getUserId():
    """
    利用session中的username
    获取userID
    :return:
    """
    if ServerConfig.SESSION_KEY_NAME in session:
        # 登录态被记住，那么直接进照片美学页面
        userName = escape(session[ServerConfig.SESSION_KEY_NAME])
        if userName:
            # 进行一个简单的哈希映射
            userId = str(hash(userName))
            return (userName,userId)

    return None


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    """
    图片上传路由
    分为：
    1.上传图片 - POST
    2.获取已经上传了的图片信息 -  GET
    :return:
    """
    if request.method == 'POST':
        """
        处理图片上传请求
        """
        files = request.files['file']
        if files:

            # 获取session中的userID
            _, user_id = getUserId()

            # 保存上传图片以及缩略图
            return_msg, img_path = ImgHandle.handlePhotoPost(files, app, user_id)

            if img_path:

                # 计算美学得分
                aes_score = AesModel.runModelForSingleImg(img_path, True)
                aes_score_str = (u"美学得分：%.2f" % aes_score)
                return_msg.aes_score = aes_score_str

                # 整体数据落db
                addAesInfo(user_id, return_msg.name, aes_score, db)

            return simplejson.dumps({"files": [return_msg.get_file()]})

    if request.method == 'GET':
        """
        处理图片信息加载请求
        """
        # 拿到用户id
        _, user_id = getUserId()
        if user_id == None or user_id == '':
            return redirect(url_for('login'))

        # 先从db中拉取出所有该用户的相关数据
        aes_score_container = queryAesInfoById(user_id)

        # 组合入回包结构体中
        file_info_return = ImgHandle.handlePhotoGet(app, aes_score_container, user_id)

        return simplejson.dumps({"files": file_info_return})




@app.route("/delete/<string:filename>", methods=['DELETE'])
def delete(filename):

    # 拿到用户id
    _, user_id = getUserId()
    if user_id == None or user_id == '':
        return redirect(url_for('login'))

    # 先拿到两个folder的具体位置
    suc , user_upload_folder, thumb_folder = ImgHandle.setup_user_cache(user_id, app)
    if not suc:
        return simplejson.dumps({filename: 'False'})

    file_path = os.path.join(user_upload_folder, filename)
    file_thumb_path = os.path.join(thumb_folder, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            if os.path.exists(file_thumb_path):
                os.remove(file_thumb_path)

            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})


@app.route("/thumbnail/<string:filename>", methods=['GET'])
def get_thumbnail(filename):
    """
    获取图片缩略图处理
    :param filename:
    :return:
    """
    # 拿到用户id
    _, user_id = getUserId()
    if user_id == None or user_id == '':
        return redirect(url_for('login'))
    # 先拿到thumbnail的具体位置
    _, _, user_thumb_folder = ImgHandle.setup_user_cache(user_id, app)
    valid, _, _ = FileUtils.valid_path(os.path.join(user_thumb_folder,filename))
    if valid:
        return send_from_directory(user_thumb_folder, filename=filename)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename='error.png')



@app.route("/data/<string:filename>", methods=['GET'])
def get_file(filename):
    """
    获取图片大图处理
    :param filename:
    :return:
    """
    # 拿到用户id
    _, user_id = getUserId()
    if user_id == None or user_id == '':
        return redirect(url_for('login'))

    # 先拿到uploadfolder的具体位置
    _, user_upload_folder, _ = ImgHandle.setup_user_cache(user_id, app)
    valid, _, _ = FileUtils.valid_path(os.path.join(user_upload_folder,filename))
    if valid:
        return send_from_directory(user_upload_folder, filename=filename)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename='error.png')



@app.route('/login', methods=['GET', 'POST'])
def login():
    return UsrHandle.handleUserLogin(request.method, session)


@app.route('/', methods=['GET', 'POST'])
def index():
    if not AesModel.initFinish():
        return render_template('invalid.html')
    if ServerConfig.SESSION_KEY_NAME in session:
        # 登录态被记住，那么直接进照片美学页面
        userName, userId = getUserId()
        if userName == None or userName == '':
            return redirect(url_for('login'))
        print('UserName recorded from session = %s id = %s' % (userName,userId))
        return render_template('index.html')
    return redirect(url_for('login'))


def create_app():
    """
    flask启动前初始化
    :return:
    """

if __name__ == '__main__':
    # 后台业务逻辑启动
    app.run(debug=True)
