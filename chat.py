from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    message = request.form['message']
    bot_response = "That's very interesting"
    return {'bot_response': bot_response}

if __name__ == '__main__':
    app.run(debug=True)