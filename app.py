import os
from flask import render_template, Flask, request, jsonify, redirect, flash, url_for ,session
from functools import wraps
from sqlalchemy import or_
from models import *
import requests as r
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.secret_key = b'\xd4w\xeb@a\x93\xb2Ol\xd1"\xab"\xf6\xefW'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        search_book = request.form["search"]
        books = Book.query.filter(or_(Book.title.like(f"%{search_book}%"), Book.author.like(f"%{search_book}%"),Book.isbn.like(f"%{search_book}%"))).all()
        if len(books) > 0:
            return render_template("index.html", books=books)
        else:
            return render_template("index.html", message="No Match Found")
    return render_template("index.html")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "Logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Log In To Acess This Page", "warning")
            return redirect(url_for('login'))
    return decorated_function

@app.route("/<int:book_id>", methods=["GET", "POST"])
@login_required
def review(book_id):
    book = Book.query.get(book_id)
    if book is None:
        return render_template("error.html", message="No Book With That ID found")
    res = r.get("https://www.goodreads.com/book/review_counts.json", params={"key":"NZfKmBZ4nABykHRv7cGfg", "isbns":book.isbn})
    if res.status_code == 200:
        data = res.json()
    if request.method == "POST":
        if session["Logged_in"] == True:
            user = User.query.filter_by(name=session["username"]).first()
            user_id = user.id
            rating = request.form["rating"]
            if rating == "":
                if res.status_code == 200:
                    return render_template("review.html", book=book, data=data)
                else:
                    return render_template("review.html", book=book)
            else:
                rate_check = Review.query.filter_by(user_id=user_id, book_id=book_id).count()
                if rate_check > 0:
                    flash("You Have Already Rated This Book", "warning")
                else:
                    rate = Review(rating=rating, user_id=user_id, book_id=book_id)
                    db.session.add(rate)
                    db.session.commit()
                    flash("Successfully Rated!!", "success")
                    print(f"Username: {user.name} Rating: {rate.rating} Book Name: {book.title}")
                    if res.status_code == 200:
                        return render_template("review.html", book=book, rate=rate, data=data)
                    else:
                        return render_template("review.html", book=book, rate=rate)
    if res.status_code == 200:
        return render_template("review.html", book=book, data=data)
    else:
        return render_template("review.html", book=book)

#Create Registration Fields
class RegistrationForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[
    DataRequired(),
    EqualTo("confirm", message="Password Does Not Match")
    ])
    confirm = PasswordField("Confirm Password")

#Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        user_check = User.query.filter_by(name=username).count()
        if user_check > 0:
            flash("Username Already Taken", "warning")
        else:
            user = User(name=username, password=password)
            db.session.add(user)
            print("Added User")
            db.session.commit()
            flash("You are Registered Successfully", "success")
            return redirect(url_for("index"))
    return render_template("register.html", form=form)

#Login Page
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        result = User.query.filter_by(name=username)
        no_of_users = result.count()
        if no_of_users > 0:
            data = result.first()
            password_db = data.password
            if sha256_crypt.verify(password, password_db):
                session["Logged_in"] = True
                session["username"] = username
                flash("Logged In Successfully", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid Password", "danger")
        else:
            flash("No user by that username", "danger")
    return render_template("login.html")

#logout Page
@app.route("/logout")
def logout():
    session.clear()
    flash("You are Logged out", "success")
    return redirect(url_for("login"))

#book API
@app.route("/api/<int:book_isbn>")
def book_api(book_isbn):
    book = Book.query.filter_by(isbn=str(book_isbn)).first()
    if book is None:
        return jsonify(Error="No Book Exist With That ISBN"), 404

    review_count = Review.query.filter_by(book_id=book.id).count()
    reviews = Review.query.filter_by(book_id=book.id).all()
    sum = 0
    for review in reviews:
        sum += review.rating
    avg_score = sum/len(reviews)

    return jsonify(
    title=book.title,
    author=book.author,
    year=book.pub_year,
    isbn=book.isbn,
    review_count=review_count,
    average_score=avg_score
    )
