# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session
from core.model.LoginForm import LoginForm
from config import ServerConfig
"""
登录处理逻辑
"""

def handleUserLogin(reqMethod, userSession):
    """
        登录处理
        这边其实没有所谓的登录处理
        :return:
        """
    form = LoginForm()
    if reqMethod == 'POST':
        if form.validate_on_submit():
            # 用户已经提交了登录表单，这里不需要过多的操作，也不要去DB判断什么，直接把userName写cookie即可
            loginName = form.userName.data
            userSession[ServerConfig.SESSION_KEY_NAME] = loginName
            print('User input -> LoginName = %s' % loginName)
            # rdl去主页面
            return redirect(url_for('index'))
        return redirect(url_for('login'))
    if reqMethod == 'GET':
        return render_template('login.html', form=form)
