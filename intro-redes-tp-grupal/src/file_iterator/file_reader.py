import logging
import os
from typing import Optional
from fiubaftp_vals import constants
from datagrams.fiuba_datagram_builder import FIUBADatagramBuilder


class FileReader:
    
    def __init__(self, path: str, update_seq_number, curr_seq_number, packet_size: int = constants.PACKET_DATA_SIZE):
        self.curr_seq_nbr = curr_seq_number
        self.increase_seq_number = update_seq_number
        self.packet_size = packet_size  
        self.file_size = os.stat(path).st_size
        self.packeted_size = 0;
        self.file = open(path, mode='rb')

    def next(self) -> Optional[tuple[bytes, int]]:
        if self.packeted_size >= self.file_size:
            return None

        bytes_to_read = min(self.file_size - self.packeted_size, self.packet_size)

        file_bytes = self.read_bytes(bytes_to_read)

        return self.create_network_packet(file_bytes)

    def has_next(self) -> bool:
        if self.packeted_size >= self.file_size:
            return False
        return True

    def read_bytes(self, bytes_to_read) -> bytes:
        read_bytes = self.file.read(bytes_to_read)
        self.packeted_size += bytes_to_read
        if self.packeted_size >= self.file_size:
            logging.warning(f"Cerrando archivo de lectura en paquete: {self.curr_seq_nbr()}")
            self.file.close()

        return read_bytes

    def create_network_packet(self, data: bytes): 
        packet = FIUBADatagramBuilder().set_packet_nbr(self.curr_seq_nbr()).set_data(data).build()
        curr_seq_number = self.curr_seq_nbr()
        self.increase_seq_number()
        return (packet, curr_seq_number)
