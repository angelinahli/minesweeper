from flask import render_template, session, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from app.forms import LoginForm, SignUpForm, StartGameForm
from app.models import User, Game

## START USER AUTHENTICATION ROUTES ##

@app.route("/login/", methods=["GET", "POST"])
def login():
    if is_logged_in():
        # if you're accidentally routed to the login page
        return redirect(url_for("index"))
    
    params = dict(title="Login", is_logged_in=False)
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

    params = dict(title="Sign Up", is_logged_in=False)
    form = SignUpForm()
    params["form"] = form
    if form.validate_on_submit():
        user = form.user
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    return render_template("signup.html", **params)

@app.route("/logout/", methods=["GET", "POST"])
def logout():
    if is_logged_in():
        logout_user()
    return redirect(url_for("index"))

## END USER AUTHENTICATION ROUTES ##

@app.route("/", methods=["GET", "POST"])
@app.route("/index/", methods=["GET", "POST"])
def index():
    params = dict(title="Minesweeper", is_logged_in=is_logged_in())
    if not is_logged_in():
        return render_template("landing.html", **params)
    
    params["user"] = current_user
    last_game = current_user.get_last_active_game()
    if last_game == None:
        return handle_start_game(params)

    params["game"] = last_game
    return render_template("play_game.html", **params)

def handle_start_game(params):
    form = StartGameForm()
    params["form"] = form
    if form.validate_on_submit():
        user_id = current_user.id
        game = Game(user_id=user_id, grid_length=form.grid_length.data)
        db.session.add(game)
        db.session.commit()

        game.initialize_game()
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("new_game.html", **params)

def is_logged_in() -> bool:
    return current_user.is_authenticated