from flask import render_template, session
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from app.forms import LoginForm, SignUpForm
from app.models import User

@app.route("/")
@app.route("/index/")
def index():
    params = dict(title="Minesweeper")
    if not is_logged_in():
        params["full_header"] = True
        return render_template("landing.html", **params)
    
    return render_template("play_game.html", **params)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if is_logged_in():
        # if you're accidentally routed to the login page
        return redirect(url_for("index"))
    
    params = dict(
        title="Login",
        full_header=True)
    form = LoginForm()
    params["form"] = form
    if form.validate_on_submit():
        user = form.user
        login_user(user, remember=form.remember_me)
        return redirect(url_for("index"))
    return render_template("login.html", **params)

@app.route("/sign_up/", methods=["GET", "POST"])
def sign_up():
    if is_logged_in():
        # if you're accidentally routed to the signup page
        return redirect(url_for("index"))
    
    params = dict(
        title="Sign Up",
        full_header=True)
    form = SignUpForm()
    params["form"] = form
    if form.validate_on_submit():
        user = form.user
        login_user(user, remember=form.remember_me)
        return redirect(url_for("index"))
    return render_template("signup.html", **params)

def is_logged_in() -> bool:
    return current_user.is_authenticated