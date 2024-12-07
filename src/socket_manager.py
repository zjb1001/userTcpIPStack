from typing import Dict, Any
from tcp_protocol import TCPProtocol
from udp_protocol import UDPProtocol

class SocketInterface:
    def create_socket(self, protocol: str):
        raise NotImplementedError

class SocketManager(SocketInterface):
    def __init__(self):
        self.sockets: Dict[str, Any] = {}

    def create_socket(self, protocol: str):
        if protocol.lower() == 'tcp':
            socket = TCPProtocol()
        elif protocol.lower() == 'udp':
            socket = UDPProtocol()
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
        
        socket_id = f"{protocol}_{id(socket)}"
        self.sockets[socket_id] = socket
        return socket_id

    def get_socket(self, socket_id: str):
        return self.sockets.get(socket_id)

    def close_socket(self, socket_id: str):
        if socket_id in self.sockets:
            self.sockets[socket_id].close()
            del self.sockets[socket_id]

    def handle_packet(self, packet: Dict[str, Any]):
        protocol = 'tcp' if packet['protocol'] == 6 else 'udp' if packet['protocol'] == 17 else None
        if not protocol:
            raise ValueError(f"Unsupported protocol: {packet['protocol']}")
        
        for socket in self.sockets.values():
            if isinstance(socket, TCPProtocol) and protocol == 'tcp':
                socket.handle_packet(packet)
            elif isinstance(socket, UDPProtocol) and protocol == 'udp':
                socket.handle_packet(packet)




