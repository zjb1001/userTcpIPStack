# UserNetStack

## Overview

UserNetStack is a user-space networking stack implementation in Python. It aims to provide a comprehensive, educational platform for understanding and experimenting with network protocols and operations at a lower level than typical application programming.

## Project Structure

```
/home/vm/Playground/userNetStack/
├── src/
│   ├── config.py
│   ├── udp_protocol.py
│   ├── socket_manager.py
│   ├── main.py
│   ├── virtual_device_manager.py
│   ├── tcp_protocol.py
│   ├── packet_parser.py
│   └── event_loop.py
├── test/
│   ├── test_tcp_protocol.py
│   ├── test_event_loop.py
│   ├── test_packet_parser.py
│   ├── test_udp_protocol.py
│   └── test_virtual_device_manager.py
└── .auto-coder/
    └── libs/
        └── llm_friendly_packages/
            └── src/
                └── example1/
                    └── main.py
```

## Project Design

状态管理:

目前的TCP状态管理已经包含了基本的TCP状态，但可以进一步完善状态转换逻辑。
可以添加更多的错误处理和异常状态，如CLOSING状态的处理。


缓冲区管理:

实现发送和接收缓冲区，支持数据的分段和重组。
添加流量控制机制，基于接收窗口大小调整发送速率。


定时器和重传机制:

实现重传定时器，支持超时重传。
添加快速重传和快速恢复算法，提高网络效率。


拥塞控制:

实现拥塞窗口（cwnd）和慢启动阈值（ssthresh）。
添加拥塞控制算法，如慢启动、拥塞避免、快速重传和快速恢复。


选项处理:

支持TCP选项的处理，如MSS（最大报文段长度）、窗口缩放、SACK（选择性确认）等。


连接管理:

完善三次握手和四次挥手的实现，包括处理各种异常情况。
实现半关闭状态的处理。


套接字API完善:

实现更多的套接字选项，如SO_RCVBUF、SO_SNDBUF等。
添加非阻塞I/O支持。
实现select/poll等I/O多路复用机制。


错误处理和异常:

完善错误码和异常处理机制。
实现ICMP错误处理。


安全性:

考虑添加基本的安全机制，如SYN cookie来防止SYN洪泛攻击。


性能优化:

实现Nagle算法和延迟确认机制。
考虑添加TCP快速打开（TFO）支持。


协议交互:

完善与IP层的交互，处理IP分片和重组。
实现ARP协议交互，用于IP地址到MAC地址的转换。


日志和调试:

添加详细的日志记录功能，便于调试和问题排查。
实现统计信息收集，如RTT估算、重传次数等。


协议扩展:

考虑支持SCTP等其他传输层协议。
为未来的协议扩展预留接口。
## Key Components

1. **Virtual Device Manager**: Interfaces with the operating system's network devices.
   - **Functionality**: Creates and manages a virtual network interface (TAP device) for sending and receiving packets.
   - **Difference from real implementation**: Uses a TAP device instead of a real network interface, which may have limitations in terms of performance and compatibility with certain network configurations.

2. **Socket Manager**: Manages network sockets for various protocols.
   - **Functionality**: Creates, manages, and closes sockets for TCP and UDP protocols.
   - **Difference from real implementation**: Implements a simplified version of socket operations, which may not include all the options and features available in a full socket API.

3. **Packet Parser**: Handles the parsing and construction of network packets.
   - **Functionality**: Parses incoming packets into structured data and constructs outgoing packets from data.
   - **Difference from real implementation**: May not handle all possible packet types or options that exist in real network traffic.

4. **TCP Protocol**: Implements the Transmission Control Protocol.
   - **Functionality**: Handles connection establishment, data transfer, and connection termination for TCP.
   - **Difference from real implementation**: Simplified state machine, may not include all TCP options, congestion control algorithms, or optimizations found in production TCP stacks.

5. **UDP Protocol**: Implements the User Datagram Protocol.
   - **Functionality**: Handles sending and receiving of UDP datagrams.
   - **Difference from real implementation**: May lack some advanced features like multicast support or certain socket options.

6. **Event Loop**: Manages asynchronous I/O operations.
   - **Functionality**: Handles multiple I/O operations concurrently using a single-threaded, event-driven approach.
   - **Difference from real implementation**: May not be as optimized for high-concurrency scenarios as production-grade event loops.

7. **Config**: Handles configuration settings for the stack.
   - **Functionality**: Manages global configuration options for the networking stack.
   - **Difference from real implementation**: May have a more limited set of configuration options compared to full-featured networking stacks.

## Features

- User-space implementation of TCP and UDP protocols
- Virtual network device interface using TAP devices
- Packet parsing and construction for IP, TCP, and UDP
- Event-driven architecture for handling network events
- Extensible design for adding new protocols or features

## Limitations and Differences from Production Implementations

1. **Performance**: As a user-space implementation, it may not achieve the same performance levels as kernel-space networking stacks.
2. **Protocol Support**: Currently limited to basic TCP and UDP. Does not support ICMP, IGMP, or other protocols found in full network stacks.
3. **Security**: May lack advanced security features and hardening present in production implementations.
4. **Scalability**: Not optimized for high-volume traffic or large numbers of concurrent connections.
5. **Compliance**: May not fully comply with all RFCs and standards related to TCP/IP implementations.
6. **Error Handling**: Simplified error handling and recovery mechanisms compared to robust, production-grade implementations.
7. **Platform Support**: Limited to platforms that support TAP devices, which may not include all operating systems.

These limitations make UserNetStack more suitable for educational purposes and prototyping rather than production use.

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/UserNetStack.git
   cd UserNetStack

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the main application:

```
python src/main.py
```

To run tests:

```
python -m unittest discover test
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is an educational project and is not intended for production use. It may not implement all security features or optimizations found in production-grade network stacks.