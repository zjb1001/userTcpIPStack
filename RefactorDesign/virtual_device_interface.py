import os
import fcntl
import struct
import subprocess
import logging
import time
from typing import Optional

# 假设这些常量已在其他地方定义
IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000
TUNSETIFF = 0x400454ca
TUNSETPERSIST = 0x400454cb

class VirtualDeviceInterface:
    def __init__(self, dev_name: Optional[str] = None, is_tun: bool = True, persist: bool = False):
        self.dev_name = dev_name
        self.is_tun = is_tun
        self.persist = persist
        self.tun_fd = None
        self._ip_address: Optional[str] = None
        self._netmask: Optional[str] = None
        self._mac_address: Optional[str] = None
        self._mtu: int = 1500
        self._packet_id = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        self._create_device()  # 在初始化时创建设备

    def _create_device(self):
        retries = 3
        while retries > 0:
            try:
                self.tun_fd = os.open("/dev/net/tun", os.O_RDWR)
                mode = IFF_TUN if self.is_tun else IFF_TAP
                if self.dev_name:
                    ifr = struct.pack('16sH', self.dev_name.encode(), mode | IFF_NO_PI)
                else:
                    ifr = struct.pack('16sH', b'\0' * 16, mode | IFF_NO_PI)
                
                ioctl_result = fcntl.ioctl(self.tun_fd, TUNSETIFF, ifr)
                self.dev_name = ioctl_result[:16].decode().strip('\x00')
                break
            except IOError as e:
                if e.errno == 16:  # Device or resource busy
                    self.logger.warning(f"Device {self.dev_name} is busy. Retrying...")
                    time.sleep(1)
                    retries -= 1
                else:
                    self.logger.error(f"Failed to create device: {e}")
                    raise
        else:
            raise IOError(f"Failed to create device {self.dev_name} after multiple attempts")

        if self.persist:
            try:
                fcntl.ioctl(self.tun_fd, TUNSETPERSIST, 1)
            except IOError as e:
                self.logger.error(f"Failed to set persistence: {e}")
                raise

        self.logger.info(f"Created {'TUN' if self.is_tun else 'TAP'} device: {self.dev_name}")

    def configure_interface(self, ip_address: str, netmask: str, mtu: int = 1500):
        self._ip_address = ip_address
        self._netmask = netmask
        self._mtu = mtu

        try:
            subprocess.run(["ip", "link", "set", self.dev_name, "up"], check=True)
            subprocess.run(["ip", "addr", "add", f"{ip_address}/{netmask}", "dev", self.dev_name], check=True)
            subprocess.run(["ip", "link", "set", self.dev_name, "mtu", str(mtu)], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to configure interface: {e}")
            raise

        if not self.is_tun:
            self._mac_address = self._get_mac_address()

        self.logger.info(f"Configured {self.dev_name} with IP: {ip_address}, Netmask: {netmask}, MTU: {mtu}")

    def _get_mac_address(self) -> Optional[str]:
        try:
            result = subprocess.run(["ip", "link", "show", self.dev_name], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "link/ether" in line:
                    return line.split()[1]
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get MAC address: {e}")
        return None

    def send_packet(self, packet: bytes) -> int:
        return os.write(self.tun_fd, packet)

    def recv_packet(self, buffer_size: int = 2048) -> bytes:
        return os.read(self.tun_fd, buffer_size)

    def close(self):
        if self.tun_fd:
            os.close(self.tun_fd)
            if self._ip_address and self._netmask:
                try:
                    subprocess.run(["ip", "addr", "del", f"{self._ip_address}/{self._netmask}", "dev", self.dev_name], check=True)
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to remove IP address: {e}")
            try:
                subprocess.run(["ip", "link", "set", self.dev_name, "down"], check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to bring down interface: {e}")
            self.logger.info(f"Closed and deconfigured {'TUN' if self.is_tun else 'TAP'} device: {self.dev_name}")

    @staticmethod
    def cleanup_interface(interface_name: str):
        try:
            subprocess.run(["ip", "link", "del", interface_name], check=True)
            logging.info(f"Cleaned up interface: {interface_name}")
        except subprocess.CalledProcessError:
            logging.warning(f"Failed to clean up interface: {interface_name}")

    def get_packet_id(self) -> int:
        self._packet_id += 1
        return self._packet_id

    def get_ip_address(self) -> Optional[str]:
        return self._ip_address

    def get_netmask(self) -> Optional[str]:
        return self._netmask

    def get_mac_address(self) -> Optional[str]:
        return self._mac_address

    def get_mtu(self) -> int:
        return self._mtu