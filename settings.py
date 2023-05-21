from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
from threading import Lock
from dbmgr import db
from configparser import ConfigParser
from enum import Enum

class UserState(Enum):
   UNDEFINED = 0
   LOGGED = 1
   CONNECTED = 2
   UNLOGGED = 3

class UserInfo:
   def __init__(self):
      state = UserState.UNDEFINED
      time = 0

#import eventlet
#eventlet.monkey_patch()

g_config = ConfigParser()
g_config.read('config.ini')

#TODO add an manager class and put these variable in it
g_users = {} #key:username value:time
g_user_rooms = {} #key:username value:room
g_dic_sids = {} #key:sid value:username
user_lock = Lock()
#key:room 

socketio = SocketIO()
log = print

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# set private key 
app.config['SECRET_KEY'] = '0x950341313543'

app.config['ENV'] = 'local'  #local or remote, remote is for heroku
app.config['HOST'] = g_config.get('LOCAL_SERVER','HOST')
app.config['PORT'] = g_config.get('LOCAL_SERVER','PORT')

#create socketio
#socketio = SocketIO(app,cors_allowed_origins="*", async_mode='eventlet')
socketio.init_app(app,cors_allowed_origins="*", async_mode='threading')


# initialize the app with the extension
db.init_app(app)


