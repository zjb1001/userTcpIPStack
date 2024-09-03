import select
from typing import Dict, Callable, List, Optional
from collections import defaultdict

class EventLoop:
    def __init__(self):
        self.handlers: Dict[int, Dict[str, Optional[Callable]]] = defaultdict(lambda: {'read': None, 'write': None, 'error': None})
        self.is_running: bool = False

    def add_handler(self, fd: int, read_handler: Optional[Callable] = None, write_handler: Optional[Callable] = None, error_handler: Optional[Callable] = None):
        self.handlers[fd]['read'] = read_handler
        self.handlers[fd]['write'] = write_handler
        self.handlers[fd]['error'] = error_handler

    def remove_handler(self, fd: int):
        if fd in self.handlers:
            del self.handlers[fd]

    def run(self):
        self.is_running = True
        while self.is_running:
            read_fds = [fd for fd, handlers in self.handlers.items() if handlers['read']]
            write_fds = [fd for fd, handlers in self.handlers.items() if handlers['write']]
            error_fds = [fd for fd, handlers in self.handlers.items() if handlers['error']]

            readable, writable, errored = select.select(read_fds, write_fds, error_fds)

            for fd in readable:
                if handler := self.handlers[fd]['read']:
                    handler(fd)
            for fd in writable:
                if handler := self.handlers[fd]['write']:
                    handler(fd)
            for fd in errored:
                if handler := self.handlers[fd]['error']:
                    handler(fd)

    def stop(self):
        self.is_running = False
        self.handlers.clear()

    def get_handlers(self) -> Dict[int, Dict[str, Optional[Callable]]]:
        return self.handlers



