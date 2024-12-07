import struct
from typing import Dict, Any

class PacketParser:
    def parse_ip_packet(self, packet: bytes) -> Dict[str, Any]:
        version_ihl = packet[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0xF
        dscp_ecn = packet[1]
        total_length = struct.unpack('!H', packet[2:4])[0]
        identification = struct.unpack('!H', packet[4:6])[0]
        flags_fragment_offset = struct.unpack('!H', packet[6:8])[0]
        ttl = packet[8]
        protocol = packet[9]
        header_checksum = struct.unpack('!H', packet[10:12])[0]
        src_ip = '.'.join(map(str, packet[12:16]))
        dst_ip = '.'.join(map(str, packet[16:20]))
        
        return {
            'version': version,
            'ihl': ihl,
            'dscp_ecn': dscp_ecn,
            'total_length': total_length,
            'identification': identification,
            'flags_fragment_offset': flags_fragment_offset,
            'ttl': ttl,
            'protocol': protocol,
            'header_checksum': header_checksum,
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'data': packet[ihl*4:]
        }

    def parse_tcp_packet(self, packet: bytes) -> Dict[str, Any]:
        src_port, dst_port = struct.unpack('!HH', packet[:4])
        seq_num = struct.unpack('!I', packet[4:8])[0]
        ack_num = struct.unpack('!I', packet[8:12])[0]
        offset_reserved_flags = struct.unpack('!H', packet[12:14])[0]
        data_offset = (offset_reserved_flags >> 12) * 4
        flags = offset_reserved_flags & 0x3F
        window_size = struct.unpack('!H', packet[14:16])[0]
        checksum = struct.unpack('!H', packet[16:18])[0]
        urgent_pointer = struct.unpack('!H', packet[18:20])[0]
        
        return {
            'src_port': src_port,
            'dst_port': dst_port,
            'seq_num': seq_num,
            'ack_num': ack_num,
            'data_offset': data_offset,
            'flags': flags,
            'window_size': window_size,
            'checksum': checksum,
            'urgent_pointer': urgent_pointer,
            'data': packet[data_offset:]
        }

    def parse_udp_packet(self, packet: bytes) -> Dict[str, Any]:
        src_port, dst_port, length, checksum = struct.unpack('!HHHH', packet[:8])
        
        return {
            'src_port': src_port,
            'dst_port': dst_port,
            'length': length,
            'checksum': checksum,
            'data': packet[8:]
        }

    def construct_ip_packet(self, data: Dict[str, Any]) -> bytes:
        header = struct.pack('!BBHHHBBH4s4s',
            (data['version'] << 4) + data['ihl'],
            data['dscp_ecn'],
            data['total_length'],
            data['identification'],
            data['flags_fragment_offset'],
            data['ttl'],
            data['protocol'],
            data['header_checksum'],
            bytes(map(int, data['src_ip'].split('.'))),
            bytes(map(int, data['dst_ip'].split('.')))
        )
        return header + data['data']

    def construct_tcp_packet(self, data: Dict[str, Any]) -> bytes:
        header = struct.pack('!HHIIBBHHH',
            data['src_port'],
            data['dst_port'],
            data['seq_num'],
            data['ack_num'],
            data['data_offset'] << 4,
            data['flags'],
            data['window_size'],
            data['checksum'],
            data['urgent_pointer']
        )
        return header + data['data']

    def construct_udp_packet(self, data: Dict[str, Any]) -> bytes:
        header = struct.pack('!HHHH',
            data['src_port'],
            data['dst_port'],
            data['length'],
            data['checksum']
        )
        return header + data['data']




