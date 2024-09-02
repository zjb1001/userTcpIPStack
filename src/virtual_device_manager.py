import os
import fcntl
import struct
import socket
from abc import ABC, abstractmethod

class NetworkInterface(ABC):
    @abstractmethod
    def read(self, length: int) -> bytes:
        pass

    @abstractmethod
    def write(self, data: bytes) -> int:
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    @abstractmethod
    def fd(self):
        pass

class VirtualDeviceInterface(NetworkInterface):
    def __init__(self, device_name):
        self.device_name = device_name
        self._fd = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack('16sH', self.device_name.encode(), 2)  # 2 for TAP
        fcntl.ioctl(self._fd, 0x400454ca, ifr)  # TUNSETIFF

    def read(self, length: int) -> bytes:
        return os.read(self._fd, length)

    def write(self, data: bytes) -> int:
        return os.write(self._fd, data)

    def close(self):
        os.close(self._fd)

    @property
    def fd(self):
        return self._fd


