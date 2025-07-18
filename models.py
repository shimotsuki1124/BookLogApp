from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class BookLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    authors = db.Column(db.String)
    thumbnail = db.Column(db.String)
    description = db.Column(db.Text)
    status = db.Column(db.String)  # "reading" または "finished"
    memo = db.Column(db.Text)      # メモ（任意）
