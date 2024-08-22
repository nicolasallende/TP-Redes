from socket import AF_INET, SOCK_DGRAM
import socket
from connection_udp.connection import Connection
import logging

from fiubaftp_vals.constants import PACKET_SIZE


class ConnectionUDP():
    def __init__(self, ip, port, max_package_size = PACKET_SIZE):
        self.max_pkg_size = max_package_size
        self.udp_socket = socket.socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.settimeout(0.2)
        self.active_connections = {}
        self.closed_connections = []
        self.ip = ip
        self.port = port
        self.bind()

    def bind(self):
        self.udp_socket.bind((str(self.ip), self.port))

    def accept(self):
        while True:
            try:
                data, address = self.udp_socket.recvfrom(self.max_pkg_size)
                conn = self.active_connections.get(address, None)
                if conn is None:
                    logging.critical(f"Creo nueva conexion")
                    conn = self.create_conn(address)
                    self.queue_data(conn, data)
                    return conn
                self.queue_data(conn, data)
            except TimeoutError:
                while len(self.closed_connections) != 0:
                    closed_conn = self.closed_connections.pop()
                    self.active_connections.pop(closed_conn)

    def create_conn(self, address):
        new_conn = Connection(self, address)
        self.active_connections[address] = new_conn
        return new_conn
    
    def queue_data(self, connection, data):
        connection.queue(data)

    def close_conn(self, address):
        self.closed_connections.append(address)

    def sendto(self, data, address):
        self.udp_socket.sendto(data, address)
