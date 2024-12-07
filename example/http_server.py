##File: /home/vm/Playground/userTcpIPStack/example/http_server.py
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from src.socket import Socket, SocketType
from src.event_loop import EventLoop

class HTTPServer:
    def __init__(self, ip, port):
        self.socket = Socket(ip, port, SocketType.TCP)
        self.socket.listen(5)
        self.event_loop = EventLoop()

    def start(self):
        self.event_loop.add_handler(self.socket.protocol.src_port, read_handler=self.handle_connection)
        print(f"HTTP Server running on {self.socket.ip}:{self.socket.port}")
        self.event_loop.run()

    def handle_connection(self, fd):
        client_socket = self.socket.accept()
        if client_socket:
            self.event_loop.add_handler(client_socket.protocol.src_port, read_handler=self.handle_request, args=(client_socket,))

    def handle_request(self, fd, client_socket):
        request = client_socket.recv(1024)
        if request:
            print(f"Received request: {request.decode('utf-8')}")
            response = self.generate_response()
            client_socket.send(response.encode('utf-8'))
        self.event_loop.remove_handler(client_socket.protocol.src_port)
        client_socket.close()

    def generate_response(self):
        return "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Hello, World!</h1></body></html>"

def main():
    server = HTTPServer('127.0.0.1', 8080)
    server.start()

if __name__ == "__main__":
    main()