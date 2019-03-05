#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

BASEDIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL",
    "sqlite:///" + os.path.join(BASEDIR, "minesweeper.db"))
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "some-super-duper-secret-key")

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "login"

from app import routes
