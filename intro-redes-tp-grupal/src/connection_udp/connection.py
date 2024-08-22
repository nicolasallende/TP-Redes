import logging
from queue import Queue
import random

from fiubaftp_vals.constants import LOSS

class Connection():

    def __init__(self, manager, address):
        self.manager = manager
        self.address = address
        self.timeout = None
        self._queue = Queue()

    def queue(self, data: bytes):
        self._queue.put(data)

    def recv(self):
        return self._queue.get(block= True, timeout = self.timeout)
    
    def settimeout(self, seconds: int):
        self.timeout = seconds

    def close(self):
        self.manager.close_conn(self.address)

    def send(self, data: bytes):
        if random.randint(0,100) < LOSS:
            logging.fatal("Paquete perdido")
            return
        self.manager.sendto(data, self.address)