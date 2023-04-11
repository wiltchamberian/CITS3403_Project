from flask import Flask, render_template

app = Flask(__name__)

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