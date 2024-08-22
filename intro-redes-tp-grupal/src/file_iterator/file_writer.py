import logging
from typing import Optional
from fiubaftp_vals.constants import WINDOW_SIZE
from datagrams.fiuba_datagram import FIUBADatagram
from datagrams.fiuba_datagram_builder import FIUBADatagramBuilder

class FileWriter():
    def __init__(self, filename: str, file_size: int, increase_seq_number, expected_seq_nbr, window_size: int = WINDOW_SIZE):
        self.increase_seq_number = increase_seq_number
        self.expected_seq_nbr = expected_seq_nbr
        self.window_size = window_size
        self.buffer: list[Optional['FIUBADatagram']] = [None for _ in range(window_size)]
        self.written_size = 0
        self.file_size = file_size
        self.file = open(filename, mode = 'wb+')

    '''
    Receives the whole network packet, writes the data either to the file or to the buffer.
    In any of these cases it generates the ACK package for it.
    '''
    def write(self, network_packet: bytes):
        datagram = FIUBADatagram(network_packet)
        return self.__write(datagram)
    
    def __write(self, datagram: 'FIUBADatagram'):
        if not self.should_write(datagram.get_packet_number()):
            return self.write_to_buffer(datagram)
        
        logging.debug(f"Escribiendo paquete numero {datagram.get_packet_number()}")
        if self.write_to_file(datagram.get_data()):
            self.increase_seq_number()

        self.write_buffer()

        return self.generate_ack(datagram.get_packet_number())

    # Write the bytes to the file
    def write_to_file(self, data: bytes | None):
        if data is None:
            logging.fatal("LLega paquete sin informacion :C")
            return False

        self.file.write(data)

        self.written_size += len(data)
            
        if self.finished(): 
            logging.warning("Termine de escribir el archivo")
            self.file.close()
        
        return True

    # Generate an ACK for the packet_nbr
    def generate_ack(self, packet_nbr: int):
        return FIUBADatagramBuilder().set_ACK(True).set_packet_nbr(packet_nbr).build()
    
    # Write the datagram to the buffer. Generate the ACK for it
    def write_to_buffer(self, datagram: 'FIUBADatagram'):
        packet_n = datagram.get_packet_number()
        self.buffer[self.get_buffer_idx(packet_n)] = datagram
        return self.generate_ack(packet_n)

    # Write all the information subsequent to the previously received and written packet. It will stop if the expected_seq_nbr is not the same, or no information has yet arrived
    def write_buffer(self):
        buffer_idx = self.get_buffer_idx(self.expected_seq_nbr())

        while self.buffer[buffer_idx] is not None and self.buffer[buffer_idx].get_packet_number() == self.expected_seq_nbr():
            logging.debug(f"Escribiendo paquete numero {self.buffer[buffer_idx].get_packet_number()} desde el buffer")
            self.write_to_file(self.buffer[buffer_idx].get_data())
            self.buffer[buffer_idx] = None
            self.increase_seq_number()
            buffer_idx = self.get_buffer_idx(self.expected_seq_nbr())
    
    # Is the expected datagram
    def should_write(self, packet_nbr: int):
        # if self.finished: return False
        if self.expected_seq_nbr() != packet_nbr:
            logging.debug(f"Paquete {packet_nbr} fuera  de orden. Escribo en el buffer.")

        return self.expected_seq_nbr() == packet_nbr
        
    # Given a datagram number, get the expected position in the buffer
    def get_buffer_idx(self, datagram_nbr: int):
        return datagram_nbr % self.window_size;

    def finished(self):
        return self.written_size >= self.file_size
    
    def write_packet(self, packet: 'FIUBADatagram' or None):
        if packet is None: 
            logging.debug("El paquete no tiene informacion")
            return None
        return self.__write(packet)
