#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import wtforms as wtf
from flask_login import current_user
from flask_wtf import FlaskForm
from typing import TypeVar, Optional
from wtforms.validators import DataRequired, EqualTo, Email, Regexp, ValidationError

from app.models import User

USER_TYPE = TypeVar("User", bound=User)

def get_user_if_exists(username: str) -> Optional[User]:
    """ returns true if username exists """
    return User.query.filter_by(username=username).first()

class CheckUsername(object):
    def __call__(self, form, field): 
        if get_user_if_exists(field.data) != None:
            raise ValidationError("Sorry - this username is taken!")

class LoginForm(FlaskForm):    
    username = wtf.StringField("Username", validators=[DataRequired()])
    password = wtf.PasswordField("Password", validators=[DataRequired()])
    remember_me = wtf.BooleanField("Remember Me")
    submit = wtf.SubmitField("Sign In")

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        fv = FlaskForm.validate(self)
        if not fv:
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user == None:
            self.username.errors = list(self.username.errors)
            self.username.errors.append("Unknown username")
            return False
        elif not user.check_password(self.password.data):
            self.password.errors = list(self.password.errors)
            self.password.errors.append("Invalid password")
            return False
        self.user = user
        return True

class SignUpForm(FlaskForm):
    username = wtf.StringField("Username", validators=[
        DataRequired(), 
        CheckUsername()])
    password = wtf.PasswordField("Password", validators=[DataRequired()])
    submit = wtf.SubmitField("Create Account")

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        fv = FlaskForm.validate(self)
        if not fv:
            return False
        user = User(username=self.username.data)
        user.set_password(self.password.data)
        self.user = user
        return True

class StartGameForm(FlaskForm):
    grid_size = wtf.IntegerField("Grid Size", validators=[DataRequired()])
    submit = wtf.SubmitField("Start Game")
