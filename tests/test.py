import requests 


def test_index():
    response = requests.get('http://localhost:5000/')
    print(response.status_code)  
    print(response.text) 

def test_register():
    data = {
        'username': 'ucd2',
        'password': 'fdMD8FMp',
        'check': 'fdMD8FMp'
    }
    response = requests.post('http://localhost:5000/register', data=data)
    print(response.status_code)  
    print(response.text) 

def test_loggin():
    data = {
        'username': 'ucd2',
        'password': 'fdMD8FMp',
    }
    response = requests.post('http://localhost:5000/loggin', data=data)
    print(response.status_code) 
    print(response.text)

def test_chat_history():
    url = 'http://localhost:5000/chat_history'
    data = {
        'search_query': '',
        'username': 'alice'
    }
    response = requests.post(url, data=data)
    print(response.status_code) 
    print(response.text)  


if __name__ == '__main__':
    test_index()
    test_register()
    test_loggin()
    test_chat_history()