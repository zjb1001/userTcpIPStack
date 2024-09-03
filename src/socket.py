from enum import Enum
from collections import deque
from tcp_protocol import TCPProtocol, TCPFlags, TCPState
from udp_protocol import UDPProtocol

class SocketType(Enum):
	TCP = 1
	UDP = 2

class Socket:
	def __init__(self, ip, port, socket_type = SocketType.TCP):
		self.ip = ip
		self.port = port
		self.socket_type = socket_type
		self.protocol = self._create_protocol()
		self.backlog = 5
		self.pending_connections = deque(maxlen=self.backlog)
		self.is_listening = False

	def _create_protocol(self):
		if self.socket_type == SocketType.TCP:
			return TCPProtocol(self.ip, self.port)
		elif self.socket_type == SocketType.UDP:
			return UDPProtocol(self.ip, self.port)
		else:
			raise ValueError(f"Unsupported socket type: {self.socket_type}")
		
	def listen(self, backlog=5):
		if self.socket_type == SocketType.TCP:
			self.backlog = backlog
			self.protocol.set_state(TCPState.LISTEN)
			self.is_listening = True
			# self.protocol.listen(backlog)
			return True
		else:
			raise NotImplementedError("Listen is only supported for TCP sockets")
		
	def accept(self):
		if self.socket_type == SocketType.TCP and self.is_listening:
			if self.pending_connections:
				new_conn = self.pending_connections.popleft(0)
				return Socket._from_protocol(new_conn)
			return None
		else:
			raise NotImplementedError("Accept is only supported for TCP sockets")

	def connect(self, dst_ip, dst_port):
		self.protocol.dst_ip   = dst_ip
		self.protocol.dst_port = dst_port

		return self.protocol.connect()
		
	def send(self, data):
		return self.protocol.send(data)
	
	def recv(self, buffer_size):
		if self.socket_type == SocketType.TCP:
			return self.protocol.get_received_data()[:buffer_size]
		
		else:
			return self.protocol.receive(buffer_size)
		
	def close(self):
		if self.socket_type == SocketType.TCP:
			self.protocol.close()
		else:
			return None  # UDP is connectionless, so no need to close
		
	def handle_packet(self, packet):
		if self.socket_type == SocketType.TCP:
			if self.is_listening and self.protocol.state == TCPState.LISTEN:
				if packet['flags'] & TCPFlags.SYN:
					new_conn = TCPProtocol(self.ip, self.port, packet['src_ip'], packet['src_port'])
					new_conn.state = TCPState.SYN_RECEIVED
					new_conn.acknowledgment_number = packet['seq_num'] + 1
					new_conn.sequence_number = packet['ack_num']
					self.pending_connections.append(new_conn)
					return new_conn._create_syn_ack_packet()
			return self.protocol.handle_packet(packet)
		else:
			return self.protocol.handle_packet(packet)

	def set_blocking(self, flag):
		# self.protocol.set_blocking(flag)
		pass

	def get_peer_name(self):
		return self.protocol.dst_ip, self.protocol.dst_port
	
	def get_sock_name(self):
		return self.ip, self.port
	
	@staticmethod
	def _from_protocol(protocol):
		if isinstance(protocol, TCPProtocol):
			socket = Socket(protocol.src_ip, protocol.src_port, SocketType.TCP)
		
		elif isinstance(protocol, UDPProtocol):
			socket = Socket(protocol.src_ip, protocol.src_port, SocketType.UDP)

		else:
			raise ValueError(f"Unsupported protocol: {protocol}")
		
		socket.protocol = protocol
		return socket


