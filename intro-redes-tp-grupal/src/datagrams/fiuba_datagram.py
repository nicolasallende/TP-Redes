import struct
from fiubaftp_vals.constants import *
from fiubaftp_vals.types import CommandType

class FIUBADatagram():

    def __init__(self, network_packet: bytes):
        
        packet_nbr, flags, data = self.unpack_network_packet(network_packet)

        self.packet_nbr = packet_nbr

        self.syn_flag = bool(flags & SYN)
        self.ack_flag = bool(flags & ACK)
        self.fin_flag = bool(flags & FIN)
        self.type = self.get_type_from_bits(flags)
        self.data = data

    def unpack_network_packet(self, network_packet: bytes):
        struct_format = f"{NETWORK_ENDIAN}{USHORT}{USHORT}"

        has_data = len(network_packet) > HEADER_SIZE_BYTES
        if has_data:
            struct_format = f"{struct_format}{len(network_packet)-HEADER_SIZE_BYTES}{BYTES}"
            return struct.unpack(struct_format, network_packet)

        packet_nbr, flags = struct.unpack(struct_format, network_packet)
        return packet_nbr, flags, bytes(0)
    
    def is_SYN(self):
        return self.syn_flag
    
    def is_ACK(self):
        return self.ack_flag
    
    def is_FIN(self):
        return self.fin_flag
    
    def is_TYP(self):
        return self.type is not None

    def protocol_type(self):
        return self.type

    def get_packet_number(self):
        return self.packet_nbr

    def get_data(self):
        return self.data if len(self.data) > 0 else None
    
    def get_type_from_bits(self, flags):
        if flags & CommandType.UPLOAD.value and flags & CommandType.DOWNLOAD.value:
            raise ValueError("Que haces flaco, Un protocolo a la vez!")
        if flags & CommandType.UPLOAD.value:
            return CommandType.UPLOAD
        if flags & CommandType.DOWNLOAD.value:
            return CommandType.DOWNLOAD
        return None
