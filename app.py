from flask import Flask, render_template
from dbmgr import *
from flask import request

# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
# initialize the app with the extension
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/user', methods=['GET', 'POST'])
def user_create():
  if request.method == "POST":
      db.create_user(request)
  return 'data_base'

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

if __name__ == "__main__":
    app.run(debug=True)