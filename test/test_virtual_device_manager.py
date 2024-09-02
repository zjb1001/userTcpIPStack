import unittest
import os
import fcntl
import struct
import errno
from unittest.mock import patch, MagicMock
from virtual_device_manager import VirtualDeviceInterface

class TestVirtualDeviceInterface(unittest.TestCase):
    @patch('os.open')
    @patch('fcntl.ioctl')
    def setUp(self, mock_ioctl, mock_open):
        self.mock_fd = 5  # Arbitrary file descriptor for testing
        mock_open.return_value = self.mock_fd
        self.device = VirtualDeviceInterface('tap0')

    def test_init(self):
        self.assertEqual(self.device.device_name, 'tap0')
        self.assertEqual(self.device._fd, self.mock_fd)

    def test_init_invalid_device_name(self):
        with self.assertRaises(ValueError):
            VirtualDeviceInterface('')  # Empty string
        with self.assertRaises(ValueError):
            VirtualDeviceInterface('a' * 17)  # Too long (> 16 characters)

    @patch('os.read')
    def test_read(self, mock_read):
        test_data = b'test data'
        mock_read.return_value = test_data
        result = self.device.read(len(test_data))
        self.assertEqual(result, test_data)
        mock_read.assert_called_once_with(self.mock_fd, len(test_data))

    @patch('os.read')
    def test_read_empty(self, mock_read):
        mock_read.return_value = b''
        result = self.device.read(10)
        self.assertEqual(result, b'')

    @patch('os.read')
    def test_read_would_block(self, mock_read):
        mock_read.side_effect = BlockingIOError()
        result = self.device.read(10)
        self.assertEqual(result, b'')

    @patch('os.write')
    def test_write(self, mock_write):
        test_data = b'test data'
        mock_write.return_value = len(test_data)
        result = self.device.write(test_data)
        self.assertEqual(result, len(test_data))
        mock_write.assert_called_once_with(self.mock_fd, test_data)

    @patch('os.write')
    def test_write_partial(self, mock_write):
        test_data = b'test data'
        mock_write.return_value = 4  # Only write part of the data
        result = self.device.write(test_data)
        self.assertEqual(result, 4)

    @patch('os.write')
    def test_write_would_block(self, mock_write):
        mock_write.side_effect = BlockingIOError()
        result = self.device.write(b'test')
        self.assertEqual(result, 0)

    @patch('os.close')
    def test_close(self, mock_close):
        self.device.close()
        mock_close.assert_called_once_with(self.mock_fd)

    def test_fd_property(self):
        self.assertEqual(self.device.fd, self.mock_fd)

    @patch('fcntl.fcntl')
    def test_set_blocking_mode(self, mock_fcntl):
        # Test setting to blocking mode
        self.device.set_blocking(True)
        mock_fcntl.assert_called_with(self.mock_fd, fcntl.F_SETFL, 0)

        # Test setting to non-blocking mode
        self.device.set_blocking(False)
        mock_fcntl.assert_called_with(self.mock_fd, fcntl.F_SETFL, os.O_NONBLOCK)

if __name__ == '__main__':
    unittest.main()


