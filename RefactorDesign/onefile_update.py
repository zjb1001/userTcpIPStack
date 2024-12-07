import os
import fcntl
import struct
import random
from enum import Enum
from typing import Tuple, List, Dict, Any

class IPAddressConverter:
    @classmethod
    def inet_aton(cls, ip: str) -> bytes:
        # Split the IP address into its components
        octets = ip.split('.')
    
        # Ensure there are exactly four octets
        if len(octets) != 4:
            raise ValueError("Invalid IP address format")
    
        # Convert each octet to an integer and validate its range
        octet_ints = []
        for octet in octets:
            octet_int = int(octet)
            if octet_int < 0 or octet_int > 255:
                raise ValueError("IP address octet out of range")
            octet_ints.append(octet_int)
    
        # Combine the octets into a single 32-bit integer and pack it into bytes
        ip_bytes = struct.pack('!BBBB', *octet_ints)
    
        return ip_bytes
    
    @classmethod
    def inet_ntoa(cls, ip_int: int) -> str:
        # Convert bytes to integer if necessary
        if isinstance(ip_int, bytes):
            ip_int = int.from_bytes(ip_int, byteorder='big')

        # Ensure the input is a 32-bit integer
        if ip_int < 0 or ip_int > 0xFFFFFFFF:
            raise ValueError("Invalid 32-bit integer for IP address")
        
        # Extract each octet from the 32-bit integer
        octets = [
            (ip_int >> 24) & 0xFF,
            (ip_int >> 16) & 0xFF,
            (ip_int >> 8) & 0xFF,
            ip_int & 0xFF
        ]
        
        # Convert each octet to a string and join them with dots
        ip_str = '.'.join(map(str, octets))
        
        return ip_str

# TUN/TAP Const
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000

class VirtualDeviceInterface:
    def __init__(self, dev_name: str, is_tun: bool = True):
        self.dev_name = dev_name
        self.is_tun = is_tun
        self.tun_fd = None
        self._create_device()
        self._ip_address = "10.0.0.1"  # 假设的IP地址
        self._packet_id = 0

    def _create_device(self):
        self.tun_fd = os.open("/dev/net/tun", os.O_RDWR)
        mode = IFF_TUN if self.is_tun else IFF_TAP
        ifr = struct.pack('16sH', self.dev_name.encode(), mode | IFF_NO_PI)
        fcntl.ioctl(self.tun_fd, TUNSETIFF, ifr)
        print(f"Created {'TUN' if self.is_tun else 'TAP'} device: {self.dev_name}")

    def send_packet(self, packet: bytes) -> int:
        return os.write(self.tun_fd, packet)

    def recv_packet(self, buffer_size: int = 2048) -> bytes:
        return os.read(self.tun_fd, buffer_size)

    def close(self):
        if self.tun_fd:
            os.close(self.tun_fd)
            print(f"Closed {'TUN' if self.is_tun else 'TAP'} device: {self.dev_name}")

    def get_packet_id(self) -> int:
        self._packet_id += 1
        return self._packet_id

    def get_ip_address(self) -> str:
        return self._ip_address

class IPLayer:
    def __init__(self, vdi: VirtualDeviceInterface):
        self.vdi = vdi

    def send(self, packet: Dict[str, Any], dest_ip: str) -> None:
        version_ihl = (4 << 4) | 5
        total_length = 20 + len(packet['data'])
        id = self.vdi.get_packet_id()
        flags_fragment_offset = 0
        ttl = 64
        protocol = 6 if 'tcp' in packet else 17
        checksum = 0
        
        src_ip = struct.unpack("!I", IPAddressConverter.inet_aton(self.vdi.get_ip_address()))[0]
        dest_ip = struct.unpack("!I", IPAddressConverter.inet_aton(dest_ip))[0]
        
        header = struct.pack('!BBHHHBBHII', 
                             version_ihl, 0, total_length, id, 
                             flags_fragment_offset, ttl, protocol, checksum,
                             src_ip, dest_ip)
        
        checksum = self._calculate_checksum(header)
        header = header[:10] + struct.pack('!H', checksum) + header[12:]
        
        ip_packet = header + self._create_transport_header(packet) + packet['data']
        self.vdi.send_packet(ip_packet)

    def recv(self) -> Dict[str, Any]:
        packet = self.vdi.recv_packet()
        
        ip_header = packet[:20]
        version_ihl, _, total_length, id, flags_fragment_offset, ttl, protocol, checksum, src_ip, dest_ip = struct.unpack('!BBHHHBBHII', ip_header)
        
        if self._calculate_checksum(ip_header) != 0:
            print("Warning: IP checksum validation failed")
        
        src_ip  = IPAddressConverter.inet_ntoa(struct.pack('!I', src_ip))
        dest_ip = IPAddressConverter.inet_ntoa(struct.pack('!I', dest_ip))
        
        transport_header, data = self._parse_transport_layer(protocol, packet[20:])
        
        return {
            "source_ip": src_ip,
            "destination_ip": dest_ip,
            "protocol": protocol,
            "id": id,
            "ttl": ttl,
            **transport_header,
            "data": data
        }

    def _calculate_checksum(self, header: bytes) -> int:
        if len(header) % 2 == 1:
            header += b'\0'
        words = struct.unpack('!%sH' % (len(header) // 2), header)
        sum = 0
        for word in words:
            sum += word
        sum = (sum >> 16) + (sum & 0xFFFF)
        sum += sum >> 16
        return ~sum & 0xFFFF

    def _create_transport_header(self, packet: Dict[str, Any]) -> bytes:
        if 'tcp' in packet:
            source_port = packet['source_port']
            dest_port = packet['destination_port']
            seq_num = packet['sequence_number']
            ack_num = packet['acknowledgement_number']
            offset_reserved = (5 << 4) | 0
            flags = (
                (packet['flags']['syn'] << 1) |
                (packet['flags']['ack'] << 4) |
                (packet['flags']['fin'] << 0)
            )
            window = 65535
            checksum = 0
            urgent_ptr = 0
            
            header = struct.pack('!HHLLBBHHH', 
                                 source_port, dest_port, seq_num, ack_num,
                                 offset_reserved, flags, window, checksum, urgent_ptr)
            
            # 计算TCP校验和
            pseudo_header = struct.pack('!4s4sBBH', 
                                        IPAddressConverter.inet_aton(packet['source_ip']),
                                        IPAddressConverter.inet_aton(packet['destination_ip']),
                                        0, packet['protocol'], len(header) + len(packet['data']))
            checksum_data = pseudo_header + header + packet['data']
            checksum = self._calculate_checksum(checksum_data)
            
            return header[:16] + struct.pack('!H', checksum) + header[18:]
        elif 'udp' in packet:
            source_port = packet['source_port']
            dest_port = packet['destination_port']
            length = 8 + len(packet['data'])  # UDP header (8 bytes) + data length
            checksum = 0  # 可以选择不使用校验和
            
            return struct.pack('!HHHH', source_port, dest_port, length, checksum)

    def _parse_transport_layer(self, protocol: int, data: bytes) -> Tuple[Dict[str, Any], bytes]:
        if protocol == 6:  # TCP
            tcp_header = data[:20]
            source_port, dest_port, seq_num, ack_num, offset_reserved, flags, window, checksum, urgent_ptr = struct.unpack('!HHLLBBHHH', tcp_header)
            
            header_length = (offset_reserved >> 4) * 4
            payload = data[header_length:]
            
            return {
                "source_port": source_port,
                "destination_port": dest_port,
                "sequence_number": seq_num,
                "acknowledgement_number": ack_num,
                "flags": {
                    "syn": (flags & 0x02) != 0,
                    "ack": (flags & 0x10) != 0,
                    "fin": (flags & 0x01) != 0
                },
                "window": window
            }, payload
        elif protocol == 17:  # UDP
            udp_header = data[:8]
            source_port, dest_port, length, checksum = struct.unpack('!HHHH', udp_header)
            payload = data[8:]
            return {
                "source_port": source_port,
                "destination_port": dest_port,
                "length": length,
                "checksum": checksum
            }, payload
        else:
            return {}, data

class TCPState(Enum):
    CLOSED = 0
    LISTEN = 1
    SYN_SENT = 2
    SYN_RECEIVED = 3
    ESTABLISHED = 4
    FIN_WAIT_1 = 5
    FIN_WAIT_2 = 6
    CLOSE_WAIT = 7
    CLOSING = 8
    LAST_ACK = 9
    TIME_WAIT = 10

class TCP:
    def __init__(self, ip_layer: IPLayer):
        self.ip_layer = ip_layer
        self.sequence_number = random.randint(0, 4294967295)
        self.acknowledgement_number = 0
        self.state = TCPState.CLOSED
        self.destination = None
        self.receive_buffer = b""
        self.send_buffer = b""
        self.connections = []
        self.backlog = 5
        self.mss = 1460
        self.source_port = random.randint(49152, 65535)

    def connect(self, address: Tuple[str, int]) -> None:
        if self.state != TCPState.CLOSED:
            raise Exception("Connection not in CLOSED state")
        
        self.destination = address
        self._set_state(TCPState.SYN_SENT)
        
        syn_packet = self._create_packet(syn=1)
        self.ip_layer.send(syn_packet, address[0])
        
        while self.state == TCPState.SYN_SENT:
            syn_ack = self.ip_layer.recv()
            if syn_ack['flags']['syn'] and syn_ack['flags']['ack']:
                self.acknowledgement_number = syn_ack['sequence_number'] + 1
                self.sequence_number += 1
                
                ack_packet = self._create_packet(ack=1)
                self.ip_layer.send(ack_packet, address[0])
                
                self._set_state(TCPState.ESTABLISHED)
            else:
                raise Exception("Connection failed")

    def listen(self, backlog: int = 5) -> None:
        if self.state != TCPState.CLOSED:
            raise Exception("Socket is not in CLOSED state")
        
        self._set_state(TCPState.LISTEN)
        self.backlog = backlog

    def accept(self) -> Tuple['TCP', Tuple[str, int]]:
        if self.state != TCPState.LISTEN:
            raise Exception("Socket is not in LISTEN state")
        
        while len(self.connections) < self.backlog:
            syn_packet = self.ip_layer.recv()
            # if syn_packet['flags']['syn']:
            if 'flags' in syn_packet and syn_packet['flags'].get('syn'):
                new_tcp = TCP(self.ip_layer)
                new_tcp._set_state(TCPState.SYN_RECEIVED)
                new_tcp.destination = (syn_packet['source_ip'], syn_packet['source_port'])
                new_tcp.acknowledgement_number = syn_packet['sequence_number'] + 1
                
                syn_ack = new_tcp._create_packet(syn=1, ack=1)
                self.ip_layer.send(syn_ack, new_tcp.destination[0])
                
                ack = self.ip_layer.recv()
                if ack['flags']['ack']:
                    new_tcp._set_state(TCPState.ESTABLISHED)
                    self.connections.append(new_tcp)
                    return new_tcp, new_tcp.destination
        
        raise Exception("Maximum backlog reached")

    def send(self, data: bytes) -> int:
        if self.state != TCPState.ESTABLISHED:
            raise Exception("Connection not established")
        
        self.send_buffer += data
        total_sent = 0
        while self.send_buffer:
            packet = self._create_packet(data=self.send_buffer[:self.mss])
            self.ip_layer.send(packet, self.destination[0])
            
            ack = self.ip_layer.recv()
            if ack['flags']['ack']:
                bytes_acked = ack['acknowledgement_number'] - self.sequence_number
                self.sequence_number = ack['acknowledgement_number']
                self.send_buffer = self.send_buffer[bytes_acked:]
                total_sent += bytes_acked
            else:
                raise Exception("Data transmission failed")
        
        return total_sent

    def recv(self, buffer_size: int) -> bytes:
        if self.state not in [TCPState.ESTABLISHED, TCPState.FIN_WAIT_1, TCPState.FIN_WAIT_2]:
            raise Exception("Connection not in a state to receive data")
        
        while len(self.receive_buffer) < buffer_size:
            packet = self.ip_layer.recv()
            if packet['flags']['fin']:
                if self.state == TCPState.ESTABLISHED:
                    self._set_state(TCPState.CLOSE_WAIT)
                elif self.state in [TCPState.FIN_WAIT_1, TCPState.FIN_WAIT_2]:
                    self._set_state(TCPState.CLOSING)
                return b""
            
            self.receive_buffer += packet['data']
            self.acknowledgement_number += len(packet['data'])
            
            ack_packet = self._create_packet(ack=1)
            self.ip_layer.send(ack_packet, self.destination[0])
        
        data = self.receive_buffer[:buffer_size]
        self.receive_buffer = self.receive_buffer[buffer_size:]
        return data

    def close(self) -> None:
        if self.state == TCPState.CLOSED:
            return
        elif self.state == TCPState.LISTEN:
            self._set_state(TCPState.CLOSED)
        elif self.state == TCPState.SYN_SENT:
            self._set_state(TCPState.CLOSED)
        elif self.state == TCPState.SYN_RECEIVED:
            fin_packet = self._create_packet(fin=1)
            self.ip_layer.send(fin_packet, self.destination[0])
            self._set_state(TCPState.FIN_WAIT_1)
        elif self.state == TCPState.ESTABLISHED:
            fin_packet = self._create_packet(fin=1)
            self.ip_layer.send(fin_packet, self.destination[0])
            self._set_state(TCPState.FIN_WAIT_1)
        elif self.state == TCPState.FIN_WAIT_1 or self.state == TCPState.FIN_WAIT_2:
            while self.state != TCPState.TIME_WAIT:
                packet = self.ip_layer.recv()
                if packet['flags']['fin']:
                    self.acknowledgement_number += 1
                    ack_packet = self._create_packet(ack=1)
                    self.ip_layer.send(ack_packet, self.destination[0])
                    self._set_state(TCPState.TIME_WAIT)
        elif self.state == TCPState.CLOSE_WAIT:
            fin_packet = self._create_packet(fin=1)
            self.ip_layer.send(fin_packet, self.destination[0])
            self._set_state(TCPState.LAST_ACK)
        elif self.state == TCPState.CLOSING:
            while self.state != TCPState.TIME_WAIT:
                packet = self.ip_layer.recv()
                if packet['flags']['ack']:
                    self._set_state(TCPState.TIME_WAIT)
        elif self.state == TCPState.LAST_ACK:
            while self.state != TCPState.CLOSED:
                packet = self.ip_layer.recv()
                if packet['flags']['ack']:
                    self._set_state(TCPState.CLOSED)
        elif self.state == TCPState.TIME_WAIT:
            import time
            time.sleep(60)  # Wait for 60 seconds instead of 2*MSL
            self._set_state(TCPState.CLOSED)

    def _create_packet(self, syn=0, ack=0, fin=0, data=b"") -> dict:
        return {
            "source_ip": self.ip_layer.vdi.get_ip_address(),
            "destination_ip": self.destination[0] if self.destination else "",
            "source_port": self.source_port,
            "destination_port": self.destination[1] if self.destination else 0,
            "sequence_number": self.sequence_number,
            "acknowledgement_number": self.acknowledgement_number,
            "flags": {
                "syn": syn,
                "ack": ack,
                "fin": fin
            },
            "data": data,
            "protocol": 6,  # TCP protocol number
            "tcp": True
        }

    def _set_state(self, new_state: TCPState) -> None:
        print(f"TCP state transition: {self.state} -> {new_state}")
        self.state = new_state

class UDP:
    def __init__(self, ip_layer: IPLayer):
        self.ip_layer = ip_layer
        self.source_port = random.randint(49152, 65535)

    def sendto(self, data: bytes, address: Tuple[str, int]) -> int:
        packet = {
            "source_ip": self.ip_layer.vdi.get_ip_address(),
            "destination_ip": address[0],
            "source_port": self.source_port,
            "destination_port": address[1],
            "data": data,
            "protocol": 17,  # UDP protocol number
            "udp": True
        }
        self.ip_layer.send(packet, address[0])
        return len(data)

    def recvfrom(self, buffer_size: int) -> Tuple[bytes, Tuple[str, int]]:
        packet = self.ip_layer.recv()
        data = packet['data'][:buffer_size]
        return data, (packet['source_ip'], packet['source_port'])

class Socket:
    def __init__(self, ip_layer: IPLayer, protocol: str):
        self.ip_layer = ip_layer
        if protocol.lower() == 'tcp':
            self.protocol = TCP(ip_layer)
        elif protocol.lower() == 'udp':
            self.protocol = UDP(ip_layer)
        else:
            raise ValueError("Unsupported protocol. Use 'tcp' or 'udp'.")

    def bind(self, address: Tuple[str, int]) -> None:
        if isinstance(self.protocol, TCP):
            self.protocol.source_port = address[1]
        elif isinstance(self.protocol, UDP):
            self.protocol.source_port = address[1]

    def connect(self, address: Tuple[str, int]) -> None:
        if isinstance(self.protocol, TCP):
            self.protocol.connect(address)
        else:
            raise NotImplementedError("UDP doesn't support connect")

    def listen(self, backlog: int = 5) -> None:
        if isinstance(self.protocol, TCP):
            self.protocol.listen(backlog)
        else:
            raise NotImplementedError("UDP doesn't support listen")

    def accept(self) -> Tuple['Socket', Tuple[str, int]]:
        if isinstance(self.protocol, TCP):
            new_tcp, address = self.protocol.accept()
            new_socket = Socket(self.ip_layer, 'tcp')
            new_socket.protocol = new_tcp
            return new_socket, address
        else:
            raise NotImplementedError("UDP doesn't support accept")

    def send(self, data: bytes) -> int:
        if isinstance(self.protocol, TCP):
            return self.protocol.send(data)
        else:
            raise NotImplementedError("Use sendto for UDP")

    def recv(self, buffer_size: int) -> bytes:
        if isinstance(self.protocol, TCP):
            return self.protocol.recv(buffer_size)
        else:
            raise NotImplementedError("Use recvfrom for UDP")

    def sendto(self, data: bytes, address: Tuple[str, int]) -> int:
        if isinstance(self.protocol, UDP):
            return self.protocol.sendto(data, address)
        else:
            raise NotImplementedError("TCP doesn't support sendto")

    def recvfrom(self, buffer_size: int) -> Tuple[bytes, Tuple[str, int]]:
        if isinstance(self.protocol, UDP):
            return self.protocol.recvfrom(buffer_size)
        else:
            raise NotImplementedError("TCP doesn't support recvfrom")

    def close(self) -> None:
        if isinstance(self.protocol, TCP):
            self.protocol.close()
        # UDP doesn't need explicit closing

    
                                       

# 示例使用
if __name__ == "__main__":
    vdi = VirtualDeviceInterface("tun0")
    ip_layer = IPLayer(vdi)

    # TCP 服务器示例
    server_socket = Socket(ip_layer, 'tcp')
    server_socket.bind(("10.0.0.1", 8080))
    server_socket.listen(5)

    import threading
    import time

    def client_thread():
        time.sleep(1)  # 确保服务器已经在监听
        client_socket = Socket(ip_layer, 'tcp')
        client_socket.connect(("10.0.0.1", 8080))
        client_socket.send(b"Hello, server!")
        response = client_socket.recv(1024)
        print(f"Received from server: {response.decode()}")
        client_socket.close()

    # 启动客户端线程
    threading.Thread(target=client_thread).start()

    client_socket, client_address = server_socket.accept()
    data = client_socket.recv(1024)
    print(f"Received from {client_address}: {data.decode()}")
    client_socket.send(b"Hello, client!")
    client_socket.close()

    server_socket.close()

    # UDP 示例
    udp_socket = Socket(ip_layer, 'udp')
    udp_socket.bind(("10.0.0.1", 9090))

    data, addr = udp_socket.recvfrom(1024)
    print(f"Received from {addr}: {data.decode()}")
    udp_socket.sendto(b"Hello, UDP client!", addr)

    udp_socket.close()

    vdi.close()