from virtual_device_manager import VirtualDeviceInterface
from socket_manager import SocketManager
from packet_parser import PacketParser
from event_loop import EventLoop
from config import Config
import logging
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

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

    def handle_accept(fd):
        try:
            client_socket, client_address = server_socket.accept()
            logger.info(f"New connection from {client_address}")
            event_loop.add_handler(client_socket.fileno(), read_handler=handle_read, write_handler=handle_write, error_handler=handle_error)
            event_loop.state = event_loop.EventLoopState.RUNNING
        except Exception as e:
            logger.error(f"Error handling accept: {e}")

    event_loop.add_handler(virtual_device.fd, read_handler=handle_read, write_handler=handle_write, error_handler=handle_error)

    # Create and set up the server socket
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_address = ('localhost', 8080)
    server_socket.bind(server_address)
    server_socket.listen(5)
    logger.info(f"Server is listening on {server_address}")

    # Add the server socket to the event loop's listen handlers
    event_loop.add_listen_handler(server_socket.fileno(), handle_accept)

    try:
        logger.info("Starting event loop in listen state...")
        event_loop.listen()
        
        logger.info("Transitioning to run state...")
        event_loop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        virtual_device.close()
        server_socket.close()
        event_loop.stop()

if __name__ == "__main__":
    main()
