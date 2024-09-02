import unittest
import struct
from src.packet_parser import PacketParser

class TestPacketParser(unittest.TestCase):
    def setUp(self):
        self.parser = PacketParser()

    def test_parse_ip_packet(self):
        mock_ip_packet = struct.pack('!BBHHHBBH4s4s', 
                                     (4 << 4) + 5, 0, 20, 0, 0, 64, 6, 0,
                                     b'\x7f\x00\x00\x01', b'\x7f\x00\x00\x01')
        result = self.parser.parse_ip_packet(mock_ip_packet)
        self.assertEqual(result['version'], 4)
        self.assertEqual(result['ihl'], 5)
        self.assertEqual(result['src_ip'], '127.0.0.1')
        self.assertEqual(result['dst_ip'], '127.0.0.1')

    def test_parse_tcp_packet(self):
        mock_tcp_packet = struct.pack('!HHIIBBHHH',
                                      1234, 80, 1000, 2000, (5 << 4), 0x02, 8192, 0, 0)
        result = self.parser.parse_tcp_packet(mock_tcp_packet)
        self.assertEqual(result['src_port'], 1234)
        self.assertEqual(result['dst_port'], 80)
        self.assertEqual(result['seq_num'], 1000)
        self.assertEqual(result['ack_num'], 2000)

    def test_parse_udp_packet(self):
        mock_udp_packet = struct.pack('!HHHH', 1234, 80, 8, 0)
        result = self.parser.parse_udp_packet(mock_udp_packet)
        self.assertEqual(result['src_port'], 1234)
        self.assertEqual(result['dst_port'], 80)
        self.assertEqual(result['length'], 8)

    def test_invalid_packets(self):
        with self.assertRaises(struct.error):
            self.parser.parse_ip_packet(b'\x45\x00\x00\x28\x1c\x39')
        with self.assertRaises(struct.error):
            self.parser.parse_tcp_packet(b'\x00\x50\x06\x94\x00\x00')
        with self.assertRaises(struct.error):
            self.parser.parse_udp_packet(b'\x00\x35\x00')

    def test_ip_packet_edge_cases(self):
        invalid_version_packet = b'\x60\x00\x00\x28\x1c\x39\x40\x00\x40\x06\x7c\xc3\x7f\x00\x00\x01\x7f\x00\x00\x01'
        parsed_packet = self.parser.parse_ip_packet(invalid_version_packet)
        self.assertNotEqual(parsed_packet['version'], 4)

        invalid_ihl_packet = b'\x44\x00\x00\x28\x1c\x39\x40\x00\x40\x06\x7c\xc3\x7f\x00\x00\x01\x7f\x00\x00\x01'
        parsed_packet = self.parser.parse_ip_packet(invalid_ihl_packet)
        self.assertLess(parsed_packet['ihl'], 5)

    def test_construct_packets(self):
        ip_data = {
            'version': 4, 'ihl': 5, 'dscp_ecn': 0, 'total_length': 20,
            'identification': 0, 'flags_fragment_offset': 0, 'ttl': 64,
            'protocol': 6, 'header_checksum': 0, 'src_ip': '127.0.0.1',
            'dst_ip': '127.0.0.1', 'data': b''
        }
        constructed_ip = self.parser.construct_ip_packet(ip_data)
        parsed_ip = self.parser.parse_ip_packet(constructed_ip)
        for key, value in ip_data.items():
            if key != 'data':
                self.assertEqual(parsed_ip[key], value)

        tcp_data = {
            'src_port': 1234, 'dst_port': 80, 'seq_num': 1000, 'ack_num': 2000,
            'data_offset': 5, 'flags': 0x02, 'window_size': 8192,
            'checksum': 0, 'urgent_pointer': 0, 'data': b''
        }
        constructed_tcp = self.parser.construct_tcp_packet(tcp_data)
        parsed_tcp = self.parser.parse_tcp_packet(constructed_tcp)
        for key, value in tcp_data.items():
            if key != 'data':
                self.assertEqual(parsed_tcp[key], value)

        udp_data = {
            'src_port': 1234, 'dst_port': 80, 'length': 8, 'checksum': 0, 'data': b''
        }
        constructed_udp = self.parser.construct_udp_packet(udp_data)
        parsed_udp = self.parser.parse_udp_packet(constructed_udp)
        for key, value in udp_data.items():
            if key != 'data':
                self.assertEqual(parsed_udp[key], value)

if __name__ == '__main__':
    unittest.main()


