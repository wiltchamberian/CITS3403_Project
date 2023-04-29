from flask import Flask, render_template
from dbmgr import *
from flask import request

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
socketio = SocketIO(app,cors_allowed_origins="*", async_mode='eventlet')


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
    print("index!")
    return render_template('send_text.html')

#this is for testing
@app.route('/debug',methods = ['POST', 'GET'])
def debug():
    return "Debug"
    

#for chatting, use long-connect
@socketio.on('connect')
def on_connect():
    print('on_connect')
    emit('connect-success', {'text': 'connected'})
    return "succuess"

@socketio.on('join')
def on_join(request):
    print('on_join')
    username = request["username"]
    room = request["room"]
    join_room(room)
    emit('join-success', {'text': f'{username} enter {room}'}, room = room)

@socketio.on('leave')
def on_leave():
    print("on_leave")
    username = request.data['username']
    room = request.data['room']
    leave_room(room)
    emit('message', {'text': f'{username} leave {room}'}, room = room)

@socketio.on('message')
def on_message(request):
    print("on_message!")
    username = request['username']
    room = request['room']
    text = request['text']
    db.receive_text(text)
    emit('message', {'username': username, 'text': text}, room = room)

@socketio.on('custom_event')
def on_custom_event(data):
    print('Custom Event:', data)
    # send back to client
    emit('custom_event_response', {'message': 'Custom event received'})

if __name__ == "__main__":
    #app.run(debug=True)
    #start server by flask-socketio
    print("Flask-SocketIO Start")
    socketio.run(app, host='0.0.0.0',port = 5000)