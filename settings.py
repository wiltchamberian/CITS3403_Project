from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
from threading import Lock
from dbmgr import db
from game import Game, socketio, log

#import eventlet
#eventlet.monkey_patch()


#TODO add an manager class and put these variable in it
users = {} #key:username value:time
g_user_rooms = {} #key:username value:room
g_dic_sids = {} #key:sid value:username
user_lock = Lock()
#key:room 
g_games = []
g_game_count = 1

#game servers
for i in range(g_game_count):
    g_games.append(Game())

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# set private key 
app.config['SECRET_KEY'] = '0x950341313543'
#create socketio
#socketio = SocketIO(app,cors_allowed_origins="*", async_mode='eventlet')
socketio.init_app(app,cors_allowed_origins="*", async_mode='threading')


# initialize the app with the extension
db.init_app(app)


