from flask_socketio import SocketIO
from threading import Lock

socketio = SocketIO()
#import eventlet
#eventlet.monkey_patch()

log = print

#TODO add an manager class and put these variable in it
users = {} #key:username value:time
g_user_rooms = {} #key:username value:room
g_dic_sids = {} #key:sid value:username
user_lock = Lock()
#key:room 
g_games = []
g_game_count = 1