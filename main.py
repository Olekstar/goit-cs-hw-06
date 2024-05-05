import http.server
import mimetypes
from pathlib import Path
from urllib.parse import urlparse, unquote_plus
import socketserver
import socket
import threading
import json
from datetime import datetime
from pymongo import MongoClient

BASE_DIR = Path(__file__).parent

# HTTP-сервер
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        router = urlparse(self.path).path
        match router:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(router[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        if self.path == "/message":
            size = int(self.headers['Content-Length'])
            data = self.rfile.read(size).decode()
            parsed_data = dict(kv.split('=') for kv in data.split('&'))
            message_data = {
                "username": unquote_plus(parsed_data['username']),
                "message": unquote_plus(parsed_data['message'])
            }
            message_data_json = json.dumps(message_data)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(('socket_server', 5000))
                sock.sendall(message_data_json.encode('utf-8'))

            self.send_response(302)
            self.send_header('Location', '/message')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_html('error.html')

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status=200):
        self.send_response(status)
        mimetype = mimetypes.guess_type(filename)[0] or 'txt/plain'
        self.send_header("Content-type", mimetype)
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())  

# Сокет-сервер
class SocketServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.client = MongoClient('mongodb://mongo:27017/')
        self.db = self.client['messages_db']
        self.collection = self.db['messages']

    def handle_data(self, data):
        message_data = json.loads(data)
        message_data['date'] = str(datetime.now())
        self.collection.insert_one(message_data)

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Socket server started at {self.host}:{self.port}")
        while True:
            client_socket, addr = server_socket.accept()
            data = client_socket.recv(1024).decode('utf-8')
            self.handle_data(data)
            client_socket.close()

def start_http_server():
    handler = MyHttpRequestHandler
    with socketserver.TCPServer(("", 3000), handler) as httpd:
        print("HTTP server started at http://localhost:3000")
        httpd.serve_forever()

def start_socket_server():
    server = SocketServer()
    server.start()

if __name__ == "__main__":
    http_thread = threading.Thread(target=start_http_server)
    socket_thread = threading.Thread(target=start_socket_server)
    http_thread.start()
    socket_thread.start()
    http_thread.join()
    socket_thread.join()
