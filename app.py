from flask import Flask, render_template, request, send_from_directory
from dbmgr import *
from game  import *
from flask import request
from chat_socket import socketio,log
from threading import Thread
from threading import Lock

from chat_socket import users, user_lock, g_dic_sids, g_games, g_game_count, g_user_rooms
#this code can't pass compile and it seems there are no modules called "module"
#from module import check_login

#from flask_cors import CORS

from flask_socketio import SocketIO, emit, join_room, leave_room

import jwt
import datetime

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# set private key 
app.config['SECRET_KEY'] = '0x950341313543'
#create socketio
#socketio = SocketIO(app,cors_allowed_origins="*", async_mode='eventlet')
socketio.init_app(app,cors_allowed_origins="*", async_mode='threading')

#game servers
for i in range(g_game_count):
    g_games.append(Game())



def check_heart():
    return
    HEART_INTERVAL = 10
    while True:
        now = time.time()
        with user_lock:
            for user, time in list(users.items()):
                if (now - users[user] > HEART_INTERVAL):
                    del users[user]
                    game.remove_player(user)
    
heart_thread = Thread(target = check_heart)
heart_thread.start()


def add_to_dict(key, value):
    with user_lock:
        users[key] = value

def get_from_dict(key):
    with user_lock:
        return users.get(key)

# initialize the app with the extension
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/user', methods=['GET', 'POST'])
def user_create():
  if request.method == "POST":
      db.create_user(request)
  return 'data_base'

"""
@app.route('/login', methods= ['POST'])
def user_login():
  # create token
  username = request.form["username"]
  password = request.form["password"]
  token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
  return {'token': token.decode('utf-8')}
"""

#code for redirecting from login page, to chat page given correct credentials.
#check_login() is a function checking if the credentials are correct.
@app.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        username = request.form["username"]
        password = request.form["password"]
        #if(check_login()):
         #   return redirect(url_for('templates' , filename='chat.html'))
        if True:
            users[username] = time.time()
        else:
            return render_template('Attemptloginpage.html')
    else:  
        return render_template('Attemptloginpage.html')


def protected():
  token = request.headers.get('Authorization')
  # check token
  try:
      decoded_token = jwt.decode(token, app.config['SECRET_KEY'])
      return {'message': 'Access granted'}, True
  except jwt.ExpiredSignatureError:
      return {'error': 'Token has expired'}, 401
  except jwt.InvalidTokenError:
      return {'error': 'Invalid token'}, 401

@app.route('/send-text', methods = ['POST'])
def save_text():
  res = db.receive_text(request)
  #deliver the text to members in the room
  
  return res

@app.route('/')
def index():
    log("index!")
    return render_template('send_text.html')

#this is for testing
@app.route('/debug',methods = ['POST', 'GET'])
def debug():
    return "Debug"
    

#for chatting, use long-connect
@socketio.on('connect')
def on_connect():
    client_id = request.sid
    log('on_connect')
    emit('connect-success', {'text': 'connected'})
    return "succuess"

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print('client disconnected with ID:', client_id)
    name = g_dic_sids[client_id]
    room = g_user_rooms[name]
    g_games[room].remove_player(name)
    if room in socketio.server.manager.rooms:
       if client_id in socketio.server.manager.rooms[room]:
           leave_room(room)
    users.pop(name, None)
    g_user_rooms.pop(name, None)
    g_dic_sids.pop(client_id, None)

@socketio.on('join')
def on_join(data):
    client_id = request.sid
    log('on_join')
    username = data["username"]
    room = data["room"]

    if room in socketio.server.manager.rooms:
        if client_id in socketio.server.manager.rooms[room]:
            emit('join-again', {'txt':'in room'},room = room)
            return
        
    #the user has been in this room
    if(g_user_rooms.get(username)== room):
        emit('join-again', {'txt':'in room'},room = room)
        return
    
    g_dic_sids[client_id] = username
    g_user_rooms[username] = room
    
    join_room(room)
    emit('join-success', {'text': f'{username} enter {room}'}, room = room)

@socketio.on('leave')
def on_leave(data):
    log("on_leave")
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {'text': f'{username} leave {room}'}, room = room)

@socketio.on('message')
def on_message(data):
    log("on_message!")
    username = data['username']
    room = data['room']
    text = data['text']
    db.receive_text(text)
    emit('message', {'username': username, 'text': text}, room = room)

@socketio.on('custom_event')
def on_custom_event(data):
    log('custom_event')
    # send back to client
    emit('custom_event_response', {'message': 'Custom event received'})

@socketio.on('heart')
def on_heart(data):
    log('on_heart')
    add_to_dict(data['user'],time.time())
    #cmds = {"type":"heart" ,"id":data["id"]}
    #game.enqueue_cmds(cmds)

############################game related################################
@socketio.on('join-game')
def on_join_game(data):
    log('join-game')
    room = data["room"]
    name = data["username"]
    #just add, if the players has been in the game, game will process it
    g_games[room].add_player(name)
    g_games[room].start(data)
      
    
@socketio.on('leave-game')
def on_leave_game(data):
    name =  data['name']
    del users[name]
    room = data['room']
    g_games[room].remove_player(name)      

@socketio.on('game-msg')
def on_game_message(data):
    room = data['room']
    log('game_message')
    cmds = data['cmds']
    g_games[room].enqueue_cmds(cmds)


if __name__ == "__main__":
    #app.run(debug=True)
    #start server by flask-socketio
    log("Flask-SocketIO Start")
    socketio.run(app, host='0.0.0.0',port = 5000)