from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

class DbMgr(SQLAlchemy): 
    def commit_s(self):
        try:
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            print('SQLAlchemyError:', e)
            self.session.rollback()
            return False

    def create_user(self, username, password_hash):
        user = User(
            username = username,
            password_hash = password_hash,
        )
        self.session.add(user)
        self.commit_s()

    def receive_text(self, txt):
        text = Text(
            text = txt
        )
        self.session.add(text)
        self.commit_s()

    #add login checking here
    def check_login(self):
        return True
    
    def create_room(self, roomName, userName):
        room = Room(
            userName = userName,
            roomName = roomName,
        )
        self.session.add(room)
        ok =  self.commit_s()
        if(ok):
            return roomName
        else:
            return ""

    def room_list(self, keyword):
        lis = []
        rooms = None
        if keyword == "":
            #rooms = self.session.query(Room).limit(10).all()
            rooms = self.session.query(Room).all()
        else:
            sql = '%' + keyword +'%'
            query = self.session.query(Room).filter(Room.roomName.like(sql))
            rooms = query.all()
            
        for room in rooms:
            lis.append(room.roomName)   
        return lis

    def add_default_administrator(self):
        self.create_user("yao","abc123")
        self.create_user("admin","admin")
        self.create_room("admin", "admin")

db = DbMgr()


#table for user info
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, unique = True, nullable = False)
    password_hash = db.Column(db.String(128))

#table for text
class Text(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    text = db.Column(db.String, unique = False, nullable = False)

#table for rooms
class Room(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    roomName = db.Column(db.String, unique = True, nullable = False)
    userName = db.Column(db.String, ForeignKey('User.username'))
            
