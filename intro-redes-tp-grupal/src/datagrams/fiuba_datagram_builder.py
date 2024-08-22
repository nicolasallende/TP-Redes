from fiubaftp_vals.constants import *
from fiubaftp_vals.types import CommandType
import struct

class FIUBADatagramBuilder():

    def __init__(self) :
        self.syn_flag = False
        self.ack_flag = False
        self.fin_flag = False
        self.typ_flag = None
        self.packet_number = 0
        self.data = bytes(0)

    def set_SYN(self, to: bool):
        self.syn_flag = to
        return self
    
    def set_ACK(self, to: bool):
        self.ack_flag = to
        return self

    def set_FIN(self, to: bool):
        self.fin_flag = to
        return self

    def set_TYP(self, type: CommandType):
        self.typ_flag = type
        return self

    def set_packet_nbr(self, nbr: int):
        if nbr > MAX_SHORT or nbr < 0: 
            raise ValueError('Range por packet number is [0, 65535]')
        self.packet_number = nbr
        return self
    
    def set_data(self, data:  bytes or None):
        self.data = data if data is not None else bytes(0)
        return self
    
    def build(self):
        flags = 0
        if self.ack_flag:
            flags = flags | ACK
        if self.syn_flag:
            flags = flags | SYN
        if self.fin_flag:
            flags = flags | FIN
        if self.typ_flag and self.typ_flag == CommandType.UPLOAD:
            flags = flags | CommandType.UPLOAD.value
        if self.typ_flag and self.typ_flag == CommandType.DOWNLOAD:
            flags = flags | CommandType.DOWNLOAD.value
        
        struct_format = f"{NETWORK_ENDIAN}{USHORT}{USHORT}"

        if len(self.data) <= 0:
            return struct.pack(struct_format, self.packet_number, flags)

        struct_format = f"{struct_format}{len(self.data)}{BYTES}"
        return struct.pack(struct_format, self.packet_number, flags, self.data)

