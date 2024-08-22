import logging
from file_iterator.file_reader import FileReader
from communicators.flight_window import FlightWindow

class Sender():
    
    def __init__(self, path, socket, update_seq_number, get_seq_number, on_FIN = lambda: None):
        self.path = path
        self.socket = socket
        self.update_seq_number = update_seq_number
        self.get_seq_number = get_seq_number
        self.on_FIN = on_FIN
    
    def upload(self):
        file_iterator = FileReader(self.path, self.update_seq_number, self.get_seq_number)

        window = FlightWindow(self.socket, on_FIN=self.on_FIN) # type: ignore
        
        window.recv_packets()

        while file_iterator.has_next():
            (network_packet, packet_n) = file_iterator.next()
            window.send(network_packet, packet_n)

        window.close()