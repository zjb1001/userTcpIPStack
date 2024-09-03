import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, project_root)

import unittest
from unittest.mock import Mock, patch
from src.socket import Socket, SocketType
from src.tcp_protocol import TCPProtocol, TCPState, TCPFlags


class TestSocketAndProtocols(unittest.TestCase):

    def setUp(self):
        self.server_ip = '192.168.1.1'
        self.server_port = 8080
        self.client_ip = '192.168.1.2'
        self.client_port = 12345

    def test_01_tcp_socket_creation(self):
        socket = Socket(self.server_ip, self.server_port, SocketType.TCP)
        self.assertIsInstance(socket, Socket)
        self.assertEqual(socket.ip, self.server_ip)
        self.assertEqual(socket.port, self.server_port)

    def test_02_tcp_socket_listen(self):
        socket = Socket(self.server_ip, self.server_port, SocketType.TCP)
        self.assertTrue(socket.listen())
        self.assertTrue(socket.is_listening)
        self.assertIs(socket.protocol.state, TCPState.LISTEN, "The state should be LISTEN")

    def test_03_tcp_connection_establishment(self):
        server_socket = Socket(self.server_ip, self.server_port, SocketType.TCP)
        client_socket = Socket(self.client_ip, self.client_port, SocketType.TCP)

        # Server listens
        server_socket.listen()

        # Client initiates connection
        syn_packet = client_socket.connect(self.server_ip, self.server_port)
        self.assertIsNotNone(syn_packet)
        self.assertEqual(syn_packet['flags'], TCPFlags.SYN)

        # Server receives SYN and responds with SYN-ACK
        syn_ack_packet = server_socket.handle_packet(syn_packet)
        self.assertIsNotNone(syn_ack_packet)
        self.assertEqual(syn_ack_packet['flags'], TCPFlags.SYN | TCPFlags.ACK)

        # Client receives SYN-ACK and sends ACK
        ack_packet = client_socket.handle_packet(syn_ack_packet)
        self.assertIsNotNone(ack_packet)
        self.assertEqual(ack_packet['flags'], TCPFlags.ACK)

        # Server receives ACK
        server_socket.handle_packet(ack_packet)

        # Check final states
        self.assertEqual(client_socket.protocol.state, TCPState.ESTABLISHED)
        self.assertEqual(len(server_socket.pending_connections), 1)

        # Server accepts the connection
        accepted_socket = server_socket.accept()
        self.assertIsNotNone(accepted_socket)
        self.assertEqual(accepted_socket.protocol.state, TCPState.ESTABLISHED)

    def test_04_tcp_data_transfer(self):
        # Assume connection is established
        server_socket = Socket(self.server_ip, self.server_port, SocketType.TCP)
        client_socket = Socket(self.client_ip, self.client_port, SocketType.TCP)
        server_socket.protocol.state = TCPState.ESTABLISHED
        client_socket.protocol.state = TCPState.ESTABLISHED

        # Client sends data
        data = b"Hello, Server!"
        data_packet = client_socket.send(data)
        self.assertIsNotNone(data_packet)
        self.assertEqual(data_packet['flags'], TCPFlags.PSH | TCPFlags.ACK)
        self.assertEqual(data_packet['data'], data)

        # Server receives data
        ack_packet = server_socket.handle_packet(data_packet)
        self.assertIsNotNone(ack_packet)
        self.assertEqual(ack_packet['flags'], TCPFlags.ACK)

        # Server reads received data
        received_data = server_socket.recv(1024)
        self.assertEqual(received_data, data)

    def test_05_tcp_connection_close(self):
        # Assume connection is established
        server_socket = Socket(self.server_ip, self.server_port, SocketType.TCP)
        client_socket = Socket(self.client_ip, self.client_port, SocketType.TCP)
        server_socket.protocol.state = TCPState.ESTABLISHED
        client_socket.protocol.state = TCPState.ESTABLISHED

        # Client initiates close
        fin_packet = client_socket.close()
        self.assertIsNotNone(fin_packet)
        self.assertEqual(fin_packet['flags'], TCPFlags.FIN | TCPFlags.ACK)

        # Server receives FIN and sends ACK
        ack_packet = server_socket.handle_packet(fin_packet)
        self.assertIsNotNone(ack_packet)
        self.assertEqual(ack_packet['flags'], TCPFlags.ACK)
        self.assertEqual(server_socket.protocol.state, TCPState.CLOSE_WAIT)

        # Server closes its end
        fin_packet = server_socket.close()
        self.assertIsNotNone(fin_packet)
        self.assertEqual(fin_packet['flags'], TCPFlags.FIN | TCPFlags.ACK)

        # Client receives FIN and sends ACK
        ack_packet = client_socket.handle_packet(fin_packet)
        self.assertIsNotNone(ack_packet)
        self.assertEqual(ack_packet['flags'], TCPFlags.ACK)

        # Check final states
        self.assertEqual(client_socket.protocol.state, TCPState.TIME_WAIT)
        self.assertEqual(server_socket.protocol.state, TCPState.LAST_ACK)

    # @patch('socket_class.UDPProtocol')
    # def test_udp_socket_creation(self, mock_udp_protocol):
    #     socket = Socket(self.server_ip, self.server_port, SocketType.UDP)
    #     self.assertIsInstance(socket.protocol, mock_udp_protocol)
    #     self.assertEqual(socket.ip, self.server_ip)
    #     self.assertEqual(socket.port, self.server_port)

    # def test_udp_listen_not_supported(self):
    #     socket = Socket(self.server_ip, self.server_port, SocketType.UDP)
    #     with self.assertRaises(NotImplementedError):
    #         socket.listen()

    # def test_udp_accept_not_supported(self):
    #     socket = Socket(self.server_ip, self.server_port, SocketType.UDP)
    #     with self.assertRaises(NotImplementedError):
    #         socket.accept()

if __name__ == '__main__':
    unittest.main()
