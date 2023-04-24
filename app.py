from flask import Flask, render_template
from dbmgr import *
from flask import request

#from flask_cors import CORS

from flask_socketio import SocketIO, emit

import jwt
import datetime

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# set private key 
app.config['SECRET_KEY'] = '0x950341313543'
#create socketio
socketio = SocketIO(app,cors_allowed_origins="*", async_mode='eventlet')

# 允许所有来源的 WebSocket 连接
#CORS(socketio, origins='*')

# initialize the app with the extension
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/user', methods=['GET', 'POST'])
def user_create():
  if request.method == "POST":
      db.create_user(request)
  return 'data_base'

@app.route('/login', methods= ['POST'])
def user_login():
  # create token
  username = request.form["username"]
  password = request.form["password"]
  token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
  return {'token': token.decode('utf-8')}


def protected():
  token = request.headers.get('Authorization')
  # 验证令牌
  try:
      decoded_token = jwt.decode(token, app.config['SECRET_KEY'])
      return {'message': 'Access granted'}, True
  except jwt.ExpiredSignatureError:
      return {'error': 'Token has expired'}, 401
  except jwt.InvalidTokenError:
      return {'error': 'Invalid token'}, 401

@app.route('/send-text', methods = ['POST'])
def receive_text():
  res = db.receive_text(request)
  #deliver the text to members in the room
  
  return res

@app.route('/')
def index():
    return "Hello World"
    return render_template('templates/base.html')

#this is for testing
@app.route('/debug',methods = ['POST', 'GET'])
def debug():
    return "Debug"
    if request.method == 'POST':
      return "Receive Post"
    if request.method == 'GET':
      return "Receive Get"
    

#for chatting, use long-connect
@socketio.on('connect')
def on_connect():
    print('Client connected')
    return "succuess"

@socketio.on('join')
def on_join():
    username = request.data['username']
    room = request.data['room']
    join_room(room)
    emit('message', {'text': f'{username} enter {room}'}, room = room)

@socketio.on('leave')
def on_leave():
    username = request.data['username']
    room = request.data['room']
    leave_room(room)
    emit('message', {'text': f'{username} leave {room}'}, room = room)

@socketio.on('message')
def on_message(data):
    data = request.get_json()
    username = data['username']
    room = data['room']
    text = data['text']
    receive_text(request)
    emit('message', {'username': username, 'text': text}, room = room)

@socketio.on('custom_event')
def on_custom_event(data):
    print('Custom Event:', data)
    # 向发送事件的客户端发送回应
    emit('custom_event_response', {'message': 'Custom event received'})

if __name__ == "__main__":
    #app.run(debug=True)
    #start server by flask-socketio
    print("Flask-SocketIO version:", )
    socketio.run(app, host='0.0.0.0',port = 5000)