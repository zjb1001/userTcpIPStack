import unittest
from unittest.mock import Mock, patch
from event_loop import EventLoop

class TestEventLoop(unittest.TestCase):
    def setUp(self):
        self.event_loop = EventLoop()

    def test_add_handler(self):
        mock_read = Mock()
        mock_write = Mock()
        mock_error = Mock()
        
        self.event_loop.add_handler(1, mock_read, mock_write, mock_error)
        
        self.assertEqual(self.event_loop.handlers[1]['read'], mock_read)
        self.assertEqual(self.event_loop.handlers[1]['write'], mock_write)
        self.assertEqual(self.event_loop.handlers[1]['error'], mock_error)

    def test_remove_handler(self):
        self.event_loop.add_handler(1, Mock())
        self.event_loop.remove_handler(1)
        self.assertNotIn(1, self.event_loop.handlers)

    @patch('select.select')
    def test_run(self, mock_select):
        mock_read = Mock()
        mock_write = Mock()
        mock_error = Mock()
        
        self.event_loop.add_handler(1, mock_read, mock_write, mock_error)
        
        mock_select.side_effect = [
            ([1], [1], [1]),  # First iteration
            ([], [], [])  # Second iteration to stop the loop
        ]
        
        def stop_loop(*args):
            self.event_loop.stop()
        
        mock_read.side_effect = stop_loop
        
        self.event_loop.run()
        
        mock_read.assert_called_once_with(1)
        mock_write.assert_called_once_with(1)
        mock_error.assert_called_once_with(1)

    def test_stop(self):
        self.event_loop.add_handler(1, Mock())
        self.event_loop.stop()
        self.assertFalse(self.event_loop.is_running)
        self.assertEqual(len(self.event_loop.handlers), 0)

    def test_get_handlers(self):
        mock_handler = Mock()
        self.event_loop.add_handler(1, mock_handler)
        handlers = self.event_loop.get_handlers()
        self.assertEqual(handlers[1]['read'], mock_handler)

if __name__ == '__main__':
    unittest.main()



