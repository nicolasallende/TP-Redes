import logging
from typing import Optional
from datagrams.fiuba_datagram import FIUBADatagram
from file_iterator.file_writer import FileWriter

class Receiver():
    
    def __init__(self, path, file_size, socket, update_seq_number, get_seq_number):
        self.path = path
        self.file_size = file_size
        self.socket = socket
        self.update_seq_number = update_seq_number
        self.get_seq_number = get_seq_number
    
    def download(self, keep_confirming_until = (False, lambda datagram: True), first_packet: Optional['FIUBADatagram'] = None):
        file_writer = FileWriter(self.path, self.file_size, self.update_seq_number, self.get_seq_number)

        if first_packet:
            logging.debug("Escribiendo el primer archivo que llego antes")
            ack_packet = file_writer.write_packet(first_packet)
            self.socket.send(ack_packet)

        while not file_writer.finished():
            packet = self.socket.recv()
            ack = file_writer.write(packet)
            self.socket.send(ack)

        while keep_confirming_until[0]:
            packet = self.socket.recv()
            if keep_confirming_until[1](FIUBADatagram(packet)):
                break
            ack = file_writer.write(packet)
            self.socket.send(ack)


