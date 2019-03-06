#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import wtforms as wtf
from flask_login import current_user
from flask_wtf import FlaskForm
from typing import TypeVar, Optional
from wtforms.validators import DataRequired, EqualTo, Email, Regexp, ValidationError

from app.models import User, Game

USER_TYPE = TypeVar("User", bound=User)

def get_user_if_exists(username: str) -> Optional[User]:
    """ returns true if username exists """
    return User.query.filter_by(username=username).first()

class CheckUsername(object):
    def __call__(self, form, field): 
        if get_user_if_exists(field.data) != None:
            raise ValidationError("This username is taken!")

class CheckCoord(object):
    def __init__(self, game):
        self.game = game

    def __call__(self, form, field):
        if not self.game.is_valid_coord(field.data):
            raise ValidationError("Invalid coordinate '{}'".format(field.data))

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
    submit = wtf.SubmitField("New Game")

class PlayMoveForm(FlaskForm):
    row = wtf.IntegerField("Row")
    col = wtf.IntegerField("Col")
    submit = wtf.SubmitField("Play Move")

    def __init__(self, game, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.game = game
        self.row_val = None
        self.col_val = None
        self.row.validators.append(CheckCoord(self.game))
        self.col.validators.append(CheckCoord(self.game))

    def validate(self):
        fv = FlaskForm.validate(self)
        if not fv:
            return False
        row = self.row.data
        col = self.col.data
        if self.game.is_valid_move(row, col):
            self.row_val = row
            self.col_val = col
            return True
        self.row.errors = list(self.row.errors)
        self.row.errors.append("Move ({}, {}) is invalid!".format(row, col))
        return False


