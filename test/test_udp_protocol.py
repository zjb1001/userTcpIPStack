import unittest
from unittest.mock import Mock, patch
from src.udp_protocol import UDPProtocol, UDPConnection

class TestUDPProtocol(unittest.TestCase):
    def setUp(self):
        self.udp_protocol = UDPProtocol()

    def test_handle_packet_new_connection(self):
        mock_packet = Mock(source_ip='192.168.1.1', source_port=12345)
        result = self.udp_protocol.handle_packet(mock_packet)
        self.assertIsNone(result)
        self.assertIn(('192.168.1.1', 12345), self.udp_protocol.connections)

    def test_handle_packet_existing_connection(self):
        mock_packet = Mock(source_ip='192.168.1.1', source_port=12345)
        self.udp_protocol.handle_packet(mock_packet)  # Create connection
        result = self.udp_protocol.handle_packet(mock_packet)  # Use existing connection
        self.assertIsNone(result)
        self.assertEqual(len(self.udp_protocol.connections), 1)

    def test_create_connection(self):
        addr = ('192.168.1.1', 12345)
        connection = self.udp_protocol._create_connection(addr)
        self.assertIsInstance(connection, UDPConnection)
        self.assertEqual(connection.remote_addr, addr)

class TestUDPConnection(unittest.TestCase):
    def setUp(self):
        self.udp_connection = UDPConnection(('192.168.1.1', 12345))

    def test_init(self):
        self.assertEqual(self.udp_connection.remote_addr, ('192.168.1.1', 12345))
        self.assertEqual(self.udp_connection.received_packets, [])

    def test_process_packet(self):
        mock_packet = Mock()
        result = self.udp_connection.process_packet(mock_packet)
        self.assertIsNone(result)
        self.assertEqual(self.udp_connection.received_packets, [mock_packet])

    @patch('src.udp_protocol.UDPConnection.send')
    def test_send(self, mock_send):
        data = b'test data'
        self.udp_connection.send(data)
        mock_send.assert_called_once_with(data)

    def test_send_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.udp_connection.send(b'test data')

if __name__ == '__main__':
    unittest.main()

