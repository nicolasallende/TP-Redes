import argparse

from socket import *
from communicators.client_protocol import ClientProtocol
import os
from connection_udp.client_connection import ClientConnection
from fiubaftp_vals.types import CommandType

HKEY_MTU_VALUE = 2048

class Client():
    def __init__(self, args: 'argparse.Namespace', type: CommandType):
        self.host = str(args.host)
        self.port = args.port
        self.type = type
        self.sv_address= (self.host, self.port)
        self.file_name: str = args.name
        self.init_path(args)
        self.init_file_size()
        self.socket = ClientConnection(self.sv_address)
    
    def init_path(self, args):
        try:
            self.file_path =  args.src
        except:
            self.file_path =  args.dst

        self.file_path = self.file_path.rstrip(os.sep)

    def init_file_size(self):
        try:
            self.file_size = os.path.getsize(self.get_file_path())
        except:
            self.file_size = 0

    def run(self):
        ClientProtocol(self, self.socket).exec()
    
    def get_file_name(self) -> str:
        return self.file_name
    
    def get_file_path(self) -> str:
        return os.path.join(self.file_path, self.file_name)
    
    def get_type(self) -> CommandType:
        return self.type

    def set_file_size(self, size: int):
        self.file_size = size

    def get_file_size(self):
        return self.file_size