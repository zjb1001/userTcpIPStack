from virtual_device_manager import VirtualDeviceInterface
from socket_manager import SocketManager
from packet_parser import PacketParser
from event_loop import EventLoop
from config import Config
import logging

def main():
    config = Config()
    logging.basicConfig(level=config.get('log_level', 'INFO'))
    logger = logging.getLogger(__name__)

    virtual_device = VirtualDeviceInterface(config.get('device_name', 'tap0'))
    socket_manager = SocketManager()
    packet_parser = PacketParser()
    event_loop = EventLoop()

    def handle_read(fd):
        try:
            packet = virtual_device.read(config.get('mtu', 1500))
            ip_packet = packet_parser.parse_ip_packet(packet)
            socket_manager.handle_packet(ip_packet)
        except Exception as e:
            logger.error(f"Error handling read: {e}")

    def handle_write(fd):
        try:
            # Implement write logic here
            pass
        except Exception as e:
            logger.error(f"Error handling write: {e}")

    def handle_error(fd):
        logger.error(f"Error on file descriptor: {fd}")

    event_loop.add_handler(virtual_device.fd, read_handler=handle_read, write_handler=handle_write, error_handler=handle_error)

    try:
        logger.info("Starting event loop...")
        event_loop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        virtual_device.close()
        event_loop.stop()

if __name__ == "__main__":
    main()



