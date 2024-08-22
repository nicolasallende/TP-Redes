import argparse
import logging
import os
from socket import *
from communicators.server_protocol import ServerProtocol

from connection_udp.connection_udp import ConnectionUDP
import threading

KB = 1024
MB = 1024 * KB
GB = 1024 * MB

class Server():
    def __init__(self, args: 'argparse.Namespace'):
        self.host = args.host
        self.port = args.port
        self.storage = args.storage
        self.max_file_size = 2 * GB
        self.threads = []

    def handle_client(self, connection):
        ServerProtocol(connection, self).exec()

    def clean_threads(self, timeout = 0.1):
        alive_threads = []
        for thread in self.threads:
            thread.join(timeout)
            if thread.is_alive():
                alive_threads.append(thread)
        self.threads = alive_threads

    def run(self):

        server = ConnectionUDP(self.host, self.port)

        while True:
            new_conn = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=[new_conn])
            self.threads.append(client_thread)
            client_thread.start()
            self.clean_threads()

    def exists_filename(self, file_name: str) -> bool:
        return os.path.isfile(self.get_path(file_name))
    
    def check_filesize(self, file_size: int) -> bool:
        return file_size < self.max_file_size;

    def get_file_size(self, file_name: str) -> int:
        try:
            return os.path.getsize(self.get_path(file_name))
        except OSError:
            logging.fatal("El Server no puede leer el tamaño del archivo {file_name}")
            return 0
    
    def get_path(self, file_name: str) -> str:
        return os.path.join(self.storage, file_name)