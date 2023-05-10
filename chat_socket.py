from flask_socketio import SocketIO
from threading import Lock

socketio = SocketIO()
#import eventlet
#eventlet.monkey_patch()

log = print

users = {}
user_lock = Lock()