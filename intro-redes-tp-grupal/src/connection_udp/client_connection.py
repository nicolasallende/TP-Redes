import logging
import random
from socket import AF_INET, SOCK_DGRAM, socket

from fiubaftp_vals.constants import LOSS, PACKET_SIZE


class ClientConnection():
    def __init__(self, sv_address):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.sv_address = sv_address

    def send(self, data:bytes):
        if random.randint(0,100) < LOSS:
            logging.fatal("Paquete perdido")
            return
        self.socket.sendto(data, self.sv_address)

    def recv(self):
        return self.socket.recv(PACKET_SIZE)
    
    def settimeout(self, seconds: int | None):
        self.socket.settimeout(seconds)