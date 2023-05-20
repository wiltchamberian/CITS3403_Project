from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# Create Flask application instance
#app = Flask(__name__) #the app has been created in settings.py, so 
from settings import app

# Configure the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

# Create SQLAlchemy database instance #the db has existed in so just import
#db = SQLAlchemy(app)
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

#with app.app_context(): this function can't be called more than once, just write a
#function and put the function in app.context() in app.py

def db_init():
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