from dbmgr import *
from flask import request, render_template, url_for, redirect, session, make_response
from settings import socketio,log, g_users, user_lock, g_dic_sids, g_user_rooms, app, db, UserState, UserInfo, g_config
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
import os
import sys

from db import db_test




with app.app_context():
    db.create_all()
    #administrator
    db.add_default_administrator()

    user = User(username='testuser', password='testpassword')

    db_test()

def check_heart():
    return
    HEART_INTERVAL = 10
    while True:
        now = time.time()
        with user_lock:
            for user, time in list(g_users.items()):
                if (now - g_users[user] > HEART_INTERVAL):
                    del g_users[user]
                    game.remove_player(user)
    
heart_thread = Thread(target = check_heart)
heart_thread.start()


def add_to_dict(key, value):
    with user_lock:
        g_users[key] = value

def get_from_dict(key):
    with user_lock:
        return g_users.get(key)


@app.route('/user', methods=['GET', 'POST'])
def user_create():
  if request.method == "POST":
      username = request.form["username"],
      password_hash = request.form["password"],
      db.create_user(username, password_hash)
  return 'data_base'


def attemptloginpage_template():
    return render_template('Attemptloginpage.html', \
                            index_page = url_for('index'),\
                            register_page = url_for('register_page'),\
                            login_page = url_for('login_page'),\
                            # user_page = url_for('user_page'),\
                            login = url_for('login'))

def register_page_template():
    return render_template('Register.html', register_page = url_for('register_page'), \
                            index_page = url_for('index'),\
                            login_page = url_for('login_page'),\
                            # user_page = url_for('user_page'),\
                            register = url_for('register'))
    
def home_page_template():
    return render_template('HomePage.html', register_page = url_for('register_page'), \
                            index_page = url_for('index'),\
                            # user_page = url_for('user_page'),\
                            login_page = url_for('login_page'))

def chat_history_template(username, messages):
    return render_template('chat_history.html', chat_history = url_for('chat_history')\
                           ,messages = messages\
                           , username = username)

def user_name_page_response(username):
    addr = app.config["HOST"]
    html = render_template('UserPage.html', username = username, \
                            server_ip = addr,\
                            history = url_for('chat_history_page'))
    response = make_response(html)
    response.set_cookie('username', username)
    return response

@app.route('/user_page', methods = ['GET', 'POST'])
def user_page():
    username = request.cookies.get('username',None)
    if username != None:
        return render_template('UserPage.html', username = username, history = url_for('chat_history_page'))
    return 

@app.route('/login_page', methods = ['GET'])
def login_page():
    return attemptloginpage_template()

#code for redirecting from login page, to chat page given correct credentials.
#check_login() is a function checking if the credentials are correct.
@app.route('/login', methods=['GET','POST'])
def login():
    username = session.get('username',None)
    password = session.get('password',None)
    if(username == None or password == None):
        username = request.form.get("username",None)
        password = request.form.get("password",None)

    #reset, session may not suitable, but works TODO
    session['username'] = None
    session['password'] = None

    if username == None or password == None:
        return attemptloginpage_template();

    log("login")
    log("username:"+username)

    if db.check_login(username, password):
        if(g_users.get(username) != None):
            return attemptloginpage_template();
        g_users[username] = UserInfo()
        g_users[username].time = time.time()
        g_users[username].state = UserState.LOGGED
        history = url_for('chat_hisotry_page')
        log(history)
        return user_name_page_response(username)
    else:
        return attemptloginpage_template();

@app.route('/register_page', methods = ['GET' ,'POST'])
def register_page():
    #username = request.cookies.get('username')

    return register_page_template()

   
                           
@app.route('/register', methods=['GET','POST'])
def register():
    username = request.form.get("username", None)
    password = request.form.get("password", None)
    check = request.form.get("check",None)
    if(username == None or password == None or check == None):
        return redirect(url_for('register_page'))
    if(password != check):
        return redirect(url_for('register_page'))
    #elif(db.check_unique(username)):
        #return redirect(url_for('register_page'))
    else:
        ok = db.create_user(username, password)
        if ok == False:
            return redirect(url_for('register_page'))
        session['username'] = username
        session['password'] = password
        return redirect(url_for('login'))
    
@app.route('/')
def index():
    return home_page_template()
    
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

#open chat_history web page
@app.route('/chat-history-page', methods=['POST', 'GET'])
def chat_history_page():
  log("chat_history")
  username = request.args.get("username", None)
  current_user = User.query.filter_by(username=username).first()
  messages = []
  if current_user is not None:
    messages = Message.query.filter_by(username=current_user.username).all()

  return render_template('chat_history.html', chat_history=url_for('chat_history'), messages=messages, username=username)

#for searching the chat history
@app.route('/chat_history',methods = ['GET','POST'])
def chat_history():
  log("chat_history")
  query = request.form.get('search_query', '')  # Get the search query from the form
  username = request.form.get('username', '')  # Get the username from the form

  current_user = User.query.filter_by(username=username).first()
  messages = []

  if current_user is not None:
    if query:  # If a search query is provided, filter the messages based on it
        messages = Message.query.filter(
             Message.username == current_user.username,
            (Message.username.contains(query)) | (Message.message.contains(query))
            ).all()
    else:  # Otherwise, retrieve all the user's messages
         messages = Message.query.filter_by(username=current_user.username).all()

  return render_template(
    'chat_history.html',
    chat_history=url_for('chat_history'),
    messages=messages,
    username=username,
    search_query=query
  )

#for chatting, use long-connect
@socketio.on('connect')
def on_connect():
    client_id = request.sid
    log('on_connect')
    username = request.args.get("username")
    info = g_users.get(username,None)
    if(info != None):
        if info.state == UserState.LOGGED:
            info.state = UserState.CONNECTED
        elif info.state == UserState.CONNECTED:
            emit('connect-failed', {'msg':'connected before'})
            return 
        elif info.state == UserState.UNDEFINED:
            emit('connect-failed', {'msg':'not logged'})
            return 
    else:
        emit('connect-failed', {'msg':'not logged'})
        return
        
    #if not loggined but connect directly, allow to login for covenient...
    g_dic_sids[client_id] = username
    g_users[username] = UserInfo()
    g_users[username].state = UserState.LOGGED
    g_users[username].time = time.time()
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
    if(room != None):
        if room in socketio.server.manager.rooms:
          if client_id in socketio.server.manager.rooms[room]:
              leave_room(room)

    g_users.pop(name, None)
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
    emit('join-success', {'text': f'{username} enter {room}', 'room': room, 'username':username }, room = room)

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
    #room = data.get('room',None)
    room = g_user_rooms.get(username, None)
    text = data.get('text','')

    if(room == None or username == None):
        log("room == None or username == None")
        return

    item = {}
    item["username"] = username 
    item["message"] = text
    item["timestamp"] = datetime.datetime.now();
    ok = db.add_messages([item])
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

    #get command params
    args = sys.argv[1:]  #skip first argument which is script name
    if "--env" in args:
        host_index = args.index("--env")
        if host_index < len(args) - 1:
            app.config["ENV"] = args[host_index + 1]
            print("ENV:", app.config["ENV"])
            if app.config["ENV"] == "remote":
                app.config["HOST"] = g_config.get('REMOTE_SERVER','HOST')
                app.config["PORT"] = os.environ.get("PORT", app.config["PORT"])
  
    host = app.config["HOST"]
    port = int(app.config["PORT"])

    log("Flask-SocketIO Start, host:{0}, port:{1}".format(app.config["HOST"],app.config["PORT"]))
    socketio.run(app, host="0.0.0.0", port = port, allow_unsafe_werkzeug = True)
