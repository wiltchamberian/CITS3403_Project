# CITS3403 Chat Application

## Description

A simple chat application built using Flask and Socket.IO. This application allows users to join chat rooms, send messages, and communicate in real-time.

## Features

- Real-time messaging: Users can send and receive messages in real-time.
- Multiple chat rooms: Users can join different chat rooms and engage in separate conversations.
- Simple and intuitive interface: The chat application provides a user-friendly interface for smooth communication.

## Installation(for windows)

1. Clone the repository: `git clone https://github.com/wiltchamberian/CITS3403_Project.git`

2. Navigate to the project directory: `cd CITS3403_Project`

3. Create virtual environment: `python -m venv venv`

4. Activate virutal environment: `venv/Scripts/activate`

5. Install the required dependencies: `pip install -r requirements.txt`


## Usage

There are two ways to use it. 
1). Firstly you can run local server and visit it on local pc.
   This is mostly for test and showing the basic functions.
   
2). Secondly you can run it on heroku, but you need an account and modify configuration.

The basic work-flow is:
1. Start the Flask development server. by `python -u app.py'

2. Open a web browser and go to `http://localhost:5000` to access the chat application.

3. Regist an account and select a chat room to join.

4. Start chatting! Type your messages in the input field and press Enter to send them. The messages will appear in the chat room in real-time.

5. To join a different chat room, search the rooms and double click the room.

6. To exit the chat application, simply close the web browser or press `Ctrl + C` in the terminal where the Flask server is running.

## Sample Data

### User Table

| username | password |
| --- | --- |
| alice | fdMD8FMp |
| bob | 63dCUTqz |
| chloe | ZDBfv9h8 |
| dan | 7hQYa7kt |
| eve | xSrh3xXZ |

### Message Table

| username | timestamp | message |
| --- | --- | --- |
| alice | 2023-05-22 09:00| hey guys whats the best pizza topping |
| bob | 2023-05-22 09:01 | definitely pepperoni |
| eve | 2023-05-22 09:02| nah pineapple all the way |
| alice | 2023-05-22 09:03| ewww pineapple |
| bob | 2023-05-22 09:04 | thats a crime |
| eve | 2023-05-22 09:05| what can i say its simply the best |

## License

This project is licensed under the MIT License. You are free to modify, distribute, and use the code for personal and commercial purposes.
