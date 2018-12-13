# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email
"""
登录表单类
"""
class LoginForm(FlaskForm):
    userName = StringField(u'名字', validators=[
                DataRequired(message= u'随便输个名字就可以了....'), Length(1, 64)])
    userSubmit = SubmitField(u'登录')