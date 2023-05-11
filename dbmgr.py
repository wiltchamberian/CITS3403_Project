from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

class DbMgr(SQLAlchemy): 
    def commit_s(self):
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            print('SQLAlchemyError:', e)
            self.session.rollback()

    def create_user(self, request):
        user = User(
            username = request.form["username"],
            password_hash = request.form["password"],
        )
        self.session.add(user)
        self.commit_s()

    def receive_text(self, txt):
        text = Text(
            text = txt
        )
        self.session.add(text)
        self.commit_s()

db = DbMgr()

#table for user info
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

#table for text
class Text(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, unique=False, nullable=False)


            