from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

from settings import app

# Configure the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

from dbmgr import User
from dbmgr import db
from dbmgr import Message

# Create Flask-Migrate instance
migrate = Migrate(app, db)

# Define sample data to be loaded into the database
user_data = [
    { 'username': 'alice',  'password': 'fdMD8FMp' },
    { 'username': 'bob',    'password': '63dCUTqz' },
    { 'username': 'chloe',  'password': 'ZDBfv9h8'},
    { 'username': 'dan',    'password': '7hQYa7kt' },
    { 'username': 'eve',    'password': 'xSrh3xXZ' }
]
message_data = [
    { 'username': 'alice', 'timestamp': datetime(2023, 5, 22, 9, 0),
        'message': 'hey guys whats the best pizza topping' },
    { 'username': 'bob', 'timestamp': datetime(2023, 5, 22, 9, 1),
        'message': 'definitely pepperoni' },
    { 'username': 'eve', 'timestamp': datetime(2023, 5, 22, 9, 2),
        'message': 'nah pineapple all the way' },
    { 'username': 'alice', 'timestamp': datetime(2023, 5, 22, 9, 3),
        'message': 'ewww pineapple' },
    { 'username': 'bob', 'timestamp': datetime(2023, 5, 22, 9, 4),
        'message': 'thats a crime' },
    { 'username': 'eve', 'timestamp': datetime(2023, 5, 22, 9, 5),
        'message': 'what can i say its simply the best' }
]


def db_test():
    # Create the tables if they don't exist
    #db.create_all()  it has been called in app.py, you can't run without it.

    # Add the users to the User table
    for item in user_data:
        user = User(username=item['username'], password=item['password'])
        db.session.add(user)
    db.commit_s()
    print("Users added successfully")

    # Load sample data into the database
    for item in message_data:
        message = Message(username=item['username'], message=item['message'], timestamp=item['timestamp'])
        db.session.add(message)
    db.commit_s()
    print("Messages loaded successfully")

    # Retrieve all messages from the database
    messages = Message.query.all()