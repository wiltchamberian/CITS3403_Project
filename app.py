from dbmgr import *
from flask import request, render_template
from settings import socketio,log, users, user_lock, g_dic_sids, g_user_rooms, app, db
from threading import Thread
from threading import Lock
#this code can't pass compile and it seems there are no modules called "module"
#from module import check_login
#from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import jwt
import datetime
import time
import json

from db import db_init

with app.app_context():
    db.create_all()
    #administrator
    db.add_default_administrator()

    user = User(username='testuser', password='testpassword')
    '''
    db.session.add(user)
    db.session.commit()
    # Create some dummy messages
    messages = [
      Text(username='user1', text='Hello', timestamp='2022-05-09 10:00:00'),
      Text(username='user2', text='Hi there', timestamp='2022-05-09 10:01:00'),
      Text(username='user1', text='How are you?', timestamp='2022-05-09 10:02:00'),
      Text(username='user2', text='I am good, thanks!', timestamp='2022-05-09 10:03:00')
    ]

    # Add the messages to the database
    db.session.add_all(messages)
    db.session.commit()
    '''

    #
    db_init()

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


@app.route('/user', methods=['GET', 'POST'])
def user_create():
  if request.method == "POST":
      username = request.form["username"],
      password_hash = request.form["password"],
      db.create_user(username, password_hash)
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
        if db.check_login():
            users[username] = time.time()
            return render_template('send_text.html', username = username)
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

@app.route('/chat_history')
def chat_history():
  current_user = User.query.filter_by(username='testuser').first()
  messages = Text.query.filter_by(username=current_user.username).all()
  return render_template('chat_history.html', messages=messages)

#for chatting, use long-connect
@socketio.on('connect')
def on_connect():
    client_id = request.sid
    log('on_connect')
    username = request.args.get("username")
    g_dic_sids[client_id] = username
    emit('connect-success', {'text': 'connected'})
    return "succuess"

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print('client disconnected with ID:', client_id)
    name = g_dic_sids.get(client_id, None)
    g_dic_sids.pop(client_id, None)
    if(name == None):
        return
    room = g_user_rooms.get(name,None)
    if(room == None):
        return

    if room in socketio.server.manager.rooms:
       if client_id in socketio.server.manager.rooms[room]:
           leave_room(room)
    users.pop(name, None)
    g_user_rooms.pop(name, None)

@socketio.on('create-room')
def on_create_room(data):
    client_id = request.sid
    log("create-room")
    userName = data.get("username",None)
    roomName = data.get("roomname",None)
    roomName = db.create_room(roomName, userName)
    emit('create-room', {'roomname': roomName}, room = request.sid)

@socketio.on('room-list')
def on_room_list(data):
    client_id = request.sid
    username = data.get("username",None)
    keyword = data.get("keyword",None)
    room_list = db.room_list(keyword)
    room_list_json = json.dumps(room_list)
    emit('room-list', room_list_json, room = client_id)
    log("room-list")

@socketio.on('join')
def on_join(data):
    client_id = request.sid
    log('on_join')
    username = data.get("username",None)
    room = data.get("room",None)

    if room in socketio.server.manager.rooms:
        if client_id in socketio.server.manager.rooms[room]:
            emit('join-again', {'txt':'in room'},room = room)
            return
        
    #the user has been in this room
    if(g_user_rooms.get(username,None)== room):
        emit('join-again', {'txt':'in room'},room = room)
        return
    
    #the user is now in another room
    if(g_user_rooms.get(username,None)!=None):
        leave_room(room)
        g_user_rooms.pop(username)
    
    g_user_rooms[username] = room
    join_room(room)
    emit('join-success', {'text': f'{username} enter {room}'}, room = room)

@socketio.on('leave')
def on_leave(data):
    log("on_leave")
    username = data.get('username',None)
    room = data.get('room',None)
    leave_room(room)
    emit('message', {'text': f'{username} leave {room}'}, room = room)

@socketio.on('message')
def on_message(data):
    log("on_message!")
    username = data.get('username',None)
    room = data.get('room',None)
    text = data.get('text',None)
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
    username = data.get('username',None)
    add_to_dict(username,time.time())
    #cmds = {"type":"heart" ,"id":data["id"]}
    #game.enqueue_cmds(cmds)


if __name__ == "__main__":
    #app.run(debug=True)
    #start server by flask-socketio
    log("Flask-SocketIO Start")
    socketio.run(app, host='0.0.0.0',port = 5000)
