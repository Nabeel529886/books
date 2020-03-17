from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)


class Book(db.Model):
    __tablename__ = "Books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    pub_year = db.Column(db.Integer, nullable=False)


class Review(db.Model):
    __tablename__ = "Reviews"
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("Books.id"), nullable=False)
