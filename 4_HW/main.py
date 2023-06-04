from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import urllib.parse
import mimetypes
import pathlib
import socket
from datetime import datetime
import json
import os


HOST = "127.0.0.1"
SERVER_PORT = 3000
SOCKET_PORT = 5000

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        run_socket_client(data_parse)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, html_page, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(html_page, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()

        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def formated_data(data):
    data_dict = {key: value for key, value in [el.split("=") for el in data.split("&")]}
    now = datetime.now()
    return {str(now): data_dict}


def run_server(server_class=HTTPServer, handler_class=MyHandler):
    server_address = (HOST, SERVER_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_socket_server(host=HOST, port=SOCKET_PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            f_data = formated_data(data.decode())
            save_to_storage(f_data)
    except KeyboardInterrupt:
        print("Socket server was stopped")
    finally:
        server_socket.close()


def run_socket_client(message):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(message.encode(), (HOST, SOCKET_PORT))
    client_socket.close()


def save_to_storage(data):
    with open("storage/data.json", "r+") as fh:
        if not fh.read():
            fh.write("{}")

    with open("storage/data.json", "r+") as fh:
        storage_data = json.load(fh)
        storage_data.update(data)
        fh.seek(0)
        json.dump(storage_data, fh)



def main():
    serv = Thread(target=run_server)
    serv.start()
    sock = Thread(target=run_socket_server)
    sock.start()
    
    if not os.path.exists('storage/data.json'):
        with open('storage/data.json', 'w') as f:
            f.write('{}')
            f.seek(0)


if __name__ == "__main__":
    main()
