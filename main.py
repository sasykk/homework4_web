import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
import json
import socket
import logging
from datetime import datetime

SOCKET_PORT = 5000
SOCKET_HOST = '127.0.0.1'
BUFFER_SIZE = 1024
BASE_DIR = Path()
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'

class HTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        logging.info(route)

        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])

                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html")

    def do_POST(self):
        size = int(self.headers['Content-Length'])
        data = self.rfile.read(size)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fr:
            self.wfile.write((fr.read()))

    def send_static(self, filename, status=200):
        self.send_response(status)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

def write_to_file(data, filename="./storage/data.json"):
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_dict = {str(datetime.now()): {k: v for k, v in
                                       [item.split("=") for item in
                                        [el for el in data_parse.split("&")]]}}
    try:
        with open(filename, "w", encoding='utf-8') as file:
            file.write(json.dumps(data_dict, ensure_ascii=False, indent=4))
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)

def http_server(host, port, server_class=HTTPServer, handler_class=HTTPHandler):
    server_address = (host, port)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def socket_server(host, port):
    socket_serv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = host, port
    socket_serv.bind(server)
    try:
        while True:
            data, address = socket_serv.recvfrom(BUFFER_SIZE)
            write_to_file(data)
            if not data:
                break

    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        socket_serv.close()

if __name__ == '__main__':
    http = Thread(target=http_server, args=(HTTP_HOST, HTTP_PORT))
    http.start()
    socket_s = Thread(target=socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_s.start()
