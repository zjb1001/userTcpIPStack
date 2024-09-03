import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


import unittest
from unittest.mock import Mock
from src.tcp_protocol import TCPProtocol, TCPState, TCPFlags

class TestTCPProtocol(unittest.TestCase):
    def setUp(self):
        self.tcp = TCPProtocol('192.168.1.1', 12345, '192.168.1.2', 80)

    def test_initial_state(self):
        self.assertEqual(self.tcp.state, TCPState.CLOSED)
        self.assertIsNotNone(self.tcp.sequence_number)
        self.assertEqual(self.tcp.acknowledgment_number, 0)

    def test_handle_syn_in_closed_state(self):
        packet = {'flags': TCPFlags.SYN, 'seq_num': 1000}
        response = self.tcp.handle_packet(packet)
        self.assertEqual(self.tcp.state, TCPState.SYN_RECEIVED)
        self.assertEqual(self.tcp.acknowledgment_number, 1001)
        self.assertEqual(response['flags'], TCPFlags.SYN | TCPFlags.ACK)

    def test_handle_syn_ack_in_syn_sent_state(self):
        self.tcp.state = TCPState.SYN_SENT
        packet = {'flags': TCPFlags.SYN | TCPFlags.ACK, 'seq_num': 2000, 'ack_num': self.tcp.sequence_number + 1}
        response = self.tcp.handle_packet(packet)
        self.assertEqual(self.tcp.state, TCPState.ESTABLISHED)
        self.assertEqual(self.tcp.acknowledgment_number, 2001)
        self.assertEqual(response['flags'], TCPFlags.ACK)

    def test_handle_ack_in_syn_received_state(self):
        self.tcp.state = TCPState.SYN_RECEIVED
        packet = {'flags': TCPFlags.ACK, 'seq_num': 3000, 'ack_num': self.tcp.sequence_number + 1}
        response = self.tcp.handle_packet(packet)
        self.assertEqual(self.tcp.state, TCPState.ESTABLISHED)
        self.assertIsNone(response)

    def test_handle_fin_in_established_state(self):
        self.tcp.state = TCPState.ESTABLISHED
        packet = {'flags': TCPFlags.FIN, 'seq_num': 4000}
        response = self.tcp.handle_packet(packet)
        self.assertEqual(self.tcp.state, TCPState.CLOSE_WAIT)
        self.assertEqual(self.tcp.acknowledgment_number, 4001)
        self.assertEqual(response['flags'], TCPFlags.ACK)

    def test_connect(self):
        response = self.tcp.connect()
        self.assertEqual(self.tcp.state, TCPState.SYN_SENT)
        self.assertEqual(response['flags'], TCPFlags.SYN)

    def test_close_from_established(self):
        self.tcp.state = TCPState.ESTABLISHED
        response = self.tcp.close()
        self.assertEqual(self.tcp.state, TCPState.FIN_WAIT_1)
        self.assertEqual(response['flags'], TCPFlags.FIN | TCPFlags.ACK)

    def test_send_data(self):
        self.tcp.state = TCPState.ESTABLISHED
        data = b'Hello, World!'
        response = self.tcp.send(data)
        self.assertIn(data, response['data'])
        self.assertEqual(response['flags'], TCPFlags.PSH | TCPFlags.ACK)

    def test_receive_data(self):
        self.tcp.state = TCPState.ESTABLISHED
        data = b'Received data'
        packet = {'data': data, 'seq_num': 5000}
        response = self.tcp.receive(packet)
        self.assertEqual(self.tcp.get_received_data(), data)
        self.assertEqual(response['flags'], TCPFlags.ACK)
        self.assertEqual(self.tcp.acknowledgment_number, 5000 + len(data))

if __name__ == '__main__':
    unittest.main()