import os
import time
import logging
from multiprocessing import Process
from virtual_device_interface import VirtualDeviceInterface

logging.basicConfig(level=logging.INFO)

def sender(interface_name):
    try:
        vdi = VirtualDeviceInterface(interface_name, is_tun=True)
        vdi.configure_interface("10.0.0.1", "255.255.255.0")
        
        # 发送 10 个测试数据包
        for i in range(10):
            test_packet = f"Test packet {i}".encode()
            vdi.send_packet(test_packet)
            logging.info(f"Sent: {test_packet}")
            time.sleep(0.1)  # 稍微延迟以确保接收进程有时间处理
    except Exception as e:
        logging.error(f"Sender error: {e}")
    finally:
        if 'vdi' in locals():
            vdi.close()

def receiver(interface_name):
    try:
        vdi = VirtualDeviceInterface(interface_name, is_tun=True)
        vdi.configure_interface("10.0.0.2", "255.255.255.0")
        
        # 接收 10 个数据包或等待 5 秒
        start_time = time.time()
        received_packets = 0
        while received_packets < 10 and (time.time() - start_time) < 5:
            packet = vdi.recv_packet()
            if packet:
                logging.info(f"Received: {packet}")
                received_packets += 1
        
        logging.info(f"Total packets received: {received_packets}")
    except Exception as e:
        logging.error(f"Receiver error: {e}")
    finally:
        if 'vdi' in locals():
            vdi.close()

def main():
    interface_name = "testif0"
    
    # 清理可能存在的旧接口
    VirtualDeviceInterface.cleanup_interface(interface_name)
    
    # 创建发送者进程
    sender_process = Process(target=sender, args=(interface_name,))
    
    # 创建接收者进程
    receiver_process = Process(target=receiver, args=(interface_name,))
    
    # 启动进程
    receiver_process.start()
    time.sleep(1)  # 给接收者一点时间来设置
    sender_process.start()
    
    # 等待进程结束
    sender_process.join()
    receiver_process.join()
    
    # 最后再次清理接口
    VirtualDeviceInterface.cleanup_interface(interface_name)

if __name__ == "__main__":
    if os.geteuid() != 0:
        logging.error("This script must be run as root.")
        exit(1)
    main()