from enum import Enum
import random
import struct

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

class TCPFlags:
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20

class TCPProtocol:
    def __init__(self, src_ip, src_port, dst_ip, dst_port):
        self.state = TCPState.CLOSED
        self.sequence_number = random.randint(0, 2**32 - 1)
        self.acknowledgment_number = 0
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.window_size = 65535
        self.mss = 1460
        self.send_buffer = []
        self.recv_buffer = []

    def handle_packet(self, packet):
        if self.state == TCPState.CLOSED:
            if packet['flags'] & TCPFlags.SYN:
                return self._handle_syn(packet)
        elif self.state == TCPState.LISTEN:
            if packet['flags'] & TCPFlags.SYN:
                return self._handle_syn(packet)
        elif self.state == TCPState.SYN_SENT:
            if packet['flags'] & TCPFlags.SYN and packet['flags'] & TCPFlags.ACK:
                return self._handle_syn_ack(packet)
        elif self.state == TCPState.SYN_RECEIVED:
            if packet['flags'] & TCPFlags.ACK:
                return self._handle_ack(packet)
        elif self.state == TCPState.ESTABLISHED:
            if packet['flags'] & TCPFlags.FIN:
                return self._handle_fin(packet)
            elif packet['flags'] & TCPFlags.ACK:
                return self._handle_ack(packet)
        elif self.state == TCPState.FIN_WAIT_1:
            if packet['flags'] & TCPFlags.FIN and packet['flags'] & TCPFlags.ACK:
                return self._handle_fin_ack(packet)
            elif packet['flags'] & TCPFlags.ACK:
                return self._handle_ack(packet)
        elif self.state == TCPState.FIN_WAIT_2:
            if packet['flags'] & TCPFlags.FIN:
                return self._handle_fin(packet)
        elif self.state == TCPState.CLOSING:
            if packet['flags'] & TCPFlags.ACK:
                return self._handle_ack(packet)
        elif self.state == TCPState.LAST_ACK:
            if packet['flags'] & TCPFlags.ACK:
                return self._handle_ack(packet)
        
        return None

    def _handle_syn(self, packet):
        self.state = TCPState.SYN_RECEIVED
        self.acknowledgment_number = packet['seq_num'] + 1
        return self._create_syn_ack_packet()

    def _handle_syn_ack(self, packet):
        self.state = TCPState.ESTABLISHED
        self.acknowledgment_number = packet['seq_num'] + 1
        self.sequence_number = packet['ack_num']
        return self._create_ack_packet()

    def _handle_ack(self, packet):
        if self.state == TCPState.SYN_RECEIVED:
            self.state = TCPState.ESTABLISHED
        elif self.state == TCPState.FIN_WAIT_1:
            self.state = TCPState.FIN_WAIT_2
        elif self.state == TCPState.CLOSING:
            self.state = TCPState.TIME_WAIT
        elif self.state == TCPState.LAST_ACK:
            self.state = TCPState.CLOSED
        
        self.sequence_number = packet['ack_num']
        return None

    def _handle_fin(self, packet):
        self.acknowledgment_number = packet['seq_num'] + 1
        if self.state == TCPState.ESTABLISHED:
            self.state = TCPState.CLOSE_WAIT
            return self._create_ack_packet()
        elif self.state == TCPState.FIN_WAIT_2:
            self.state = TCPState.TIME_WAIT
            return self._create_ack_packet()

    def _handle_fin_ack(self, packet):
        self.acknowledgment_number = packet['seq_num'] + 1
        self.state = TCPState.TIME_WAIT
        return self._create_ack_packet()

    def _create_syn_ack_packet(self):
        return self._create_packet(TCPFlags.SYN | TCPFlags.ACK)

    def _create_ack_packet(self):
        return self._create_packet(TCPFlags.ACK)

    def _create_fin_packet(self):
        return self._create_packet(TCPFlags.FIN | TCPFlags.ACK)

    def _create_packet(self, flags):
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'seq_num': self.sequence_number,
            'ack_num': self.acknowledgment_number,
            'flags': flags,
            'window_size': self.window_size,
            'data': b''
        }

    def connect(self):
        if self.state == TCPState.CLOSED:
            self.state = TCPState.SYN_SENT
            return self._create_packet(TCPFlags.SYN)
        return None

    def close(self):
        if self.state == TCPState.ESTABLISHED:
            self.state = TCPState.FIN_WAIT_1
            return self._create_fin_packet()
        elif self.state == TCPState.CLOSE_WAIT:
            self.state = TCPState.LAST_ACK
            return self._create_fin_packet()
        return None

    def send(self, data):
        if self.state == TCPState.ESTABLISHED:
            self.send_buffer.extend(data)
            return self._create_data_packet()
        return None

    def _create_data_packet(self):
        data = bytes(self.send_buffer[:self.mss])
        self.send_buffer = self.send_buffer[self.mss:]
        packet = self._create_packet(TCPFlags.PSH | TCPFlags.ACK)
        packet['data'] = data
        return packet

    def receive(self, packet):
        if self.state == TCPState.ESTABLISHED:
            self.recv_buffer.extend(packet['data'])
            self.acknowledgment_number += len(packet['data'])
            return self._create_ack_packet()
        return None

    def get_received_data(self):
        data = bytes(self.recv_buffer)
        self.recv_buffer.clear()
        return data


