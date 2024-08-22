import logging
from queue import Empty
import threading, time
from datagrams.fiuba_datagram import FIUBADatagram
from fiubaftp_vals import constants


class InFlight:
    def __init__(self, packet, timer, packet_nbr):
        self.number = packet_nbr
        self.packet = packet
        self.timer = timer
        # Made by the british gurl
        self.cancelled = False

    def start_timer(self):
        self.timer.start()

    def cancel_timer(self):
        self.timer.cancel()
        self.cancelled = True

class FlightWindow:
    def __init__(self, socket , on_FIN = lambda : None, size: int = constants.WINDOW_SIZE):
        self.socket = socket
        self.size = size
        self.in_flight_queue = []
        self.in_flight = {}
        self.in_flight_mutex = threading.Lock()
        self.receiver_thread: threading.Thread
        self.on_FIN = on_FIN
    
    def send_packet(self, packet):
        self.socket.send(packet)
    
    def send(self, packet, packet_n):
        while self.is_full(): 
            logging.debug(f"Ventana llena: {self.in_flight_queue}")
            time.sleep(1)
            continue

        logging.debug(f"Enviando paquete numero {packet_n}")
        self.send_packet(packet)

        self.add_packet(packet, packet_n)
    
    def add_packet(self, packet, packet_nbr):
        self.in_flight_mutex.acquire()
        self.in_flight_queue.append(packet_nbr)

        in_flight = InFlight(packet, threading.Timer(constants.PACKET_TIMER, self.resend_packet, args = [packet_nbr]), packet_nbr)

        self.in_flight[in_flight.number] = in_flight

        in_flight.start_timer()
        self.in_flight_mutex.release()

    def resend_packet(self, seq_nbr):
        logging.info(f"Resending packet {seq_nbr}")
        self.in_flight_mutex.acquire()
        self.send_packet(self.in_flight[seq_nbr].packet)
        self.in_flight[seq_nbr].timer = threading.Timer(constants.PACKET_TIMER, self.resend_packet, args = [seq_nbr])
        self.in_flight[seq_nbr].start_timer()
        self.in_flight_mutex.release()
    
    def is_full(self):
        self.in_flight_mutex.acquire()
        is_full = (len(self.in_flight_queue) == self.size)
        self.in_flight_mutex.release()
        
        return is_full

    def is_empty(self):
        self.in_flight_mutex.acquire()
        is_empty = (len(self.in_flight_queue) == 0)
        self.in_flight_mutex.release()
        
        return is_empty

    def is_window_top(self, seq_nbr):
        self.in_flight_mutex.acquire()
        logging.debug(f"Numero de paquete {seq_nbr} Window: {self.in_flight_queue}")
        response = (len(self.in_flight_queue) != 0 and self.in_flight_queue[0] == seq_nbr)
        self.in_flight_mutex.release()
        return response

    def move_window(self):
        logging.debug("Comienza el movimiento de la ventana")
        self.in_flight_mutex.acquire()
        queue_not_empty = lambda : len(self.in_flight_queue) != 0

        window_top_timer_canceled = lambda : self.in_flight[self.in_flight_queue[0]].cancelled

        while queue_not_empty() and window_top_timer_canceled():
            self.in_flight.pop(self.in_flight_queue.pop(0))
        
        logging.debug(f"Estado de la ventana despues del movimiento: {self.in_flight_queue}")

        self.in_flight_mutex.release()

    def cancel_timer(self, seq_nbr):
        self.in_flight_mutex.acquire()
        in_flight = self.in_flight.get(seq_nbr, None)
        
        if in_flight is not None:
            logging.info(f"Timer cancelado para el paquete {seq_nbr}")
            in_flight.cancel_timer()
        self.in_flight_mutex.release()
    
    def handle_receiver(self):
        self.socket.settimeout(1)
        while self.size > 0:
            try:
                ack_packet = self.socket.recv()

                datagram = FIUBADatagram(ack_packet)

                seq_nbr = datagram.get_packet_number()

                if datagram.is_FIN():
                    self.on_FIN()
                    logging.warning("Recibi FIN: tengo el archivo completo")
                    break
                if not datagram.is_ACK():
                    logging.fatal("ACK no recibido")
                    continue

                self.cancel_timer(seq_nbr)

                if self.is_window_top(seq_nbr): 
                    logging.debug("Tope de ventana alcanzado")
                    self.move_window()
            except (Empty, TimeoutError) as _:
                pass
        
        logging.debug("Terminando thread de receiver")
        self.socket.settimeout(None)
        self.clean_all()

    def clean_all(self):
        self.in_flight_mutex.acquire()
        for pkg in self.in_flight:
            self.in_flight[pkg].cancel_timer()
        self.in_flight_queue = []
        self.in_flight.clear()
        self.in_flight_mutex.release()

    def recv_packets(self):
        self.receiver_thread = threading.Thread(target = self.handle_receiver)
        self.receiver_thread.start()
    
    def close(self):
        while not self.is_empty(): continue

        logging.debug("Cerrando Flight Window")
        self.size = 0
        logging.debug("Tamaño de ventana en 0, join thread")
        self.receiver_thread.join()
