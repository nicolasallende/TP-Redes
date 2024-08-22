from enum import Enum
import logging
from queue import Empty
from typing import Optional
from communicators.protocol import Protocol
from communicators.receiver import Receiver
from communicators.sender import Sender
from datagrams.fiuba_datagram import FIUBADatagram
from datagrams.fiuba_datagram_builder import FIUBADatagramBuilder
from fiubaftp_vals.types import CommandType


class ConnHSType(Enum):
    FIN = 'Fin'
    TYP = 'Typ'
    ACK = 'Ack'

class ServerProtocol(Protocol):

    def __init__(self, connection, server):
        super().__init__()
        self.socket = connection
        self.server = server
        self.set_package_number(0)
        self.file_name: Optional[str] = None
        self.file_size: Optional[int] = None

    def exec(self):
        hstype, data = self.connection_handshake()

        result = None 
        match hstype:
            case ConnHSType.FIN:
                logging.debug("HS terminado en FIN")
                self.close()
                return
            case ConnHSType.TYP:
                logging.debug("HS continua con TYP")
                result = self.file_handshake(data)
            case ConnHSType.ACK:
                logging.debug("HS para el TYP")
                result = self.file_handshake()

        if result: 
            logging.debug(f"Empezando la ejecucion de la transferencia")
            self.execute_transfer(result)

        logging.debug(f"Termina la ejecucion de la transferencia")

        self.close()

    def connection_handshake(self):
        logging.warning("Comienza el Handshake")        
        datagram = self.recv_parse()
        if not datagram.is_SYN():
            logging.debug("Recibi primer paquete no SYN. Terminando")
            return (ConnHSType.FIN, None)

        return self.send_SYNACK()
    
    def send_SYNACK(self):
        logging.debug("Enviando SYN-ACK")
        response = self.get_SYNACK()
        self.socket.send(response)
        return self.expect_ACK()
    
    def expect_ACK(self):
        logging.debug("Esperando ACK del cliente")
        datagram = self.recv_parse()
        if not datagram.is_ACK():
            if datagram.is_SYN():
                logging.debug("Recibo otro SYN. Reenvio SYN-ACK")
                return self.send_SYNACK()
            elif datagram.is_TYP() and datagram.get_packet_number() == self.get_package_number():
                logging.debug("Recibo un TYP. Se perdio SYN-ACK pero llego mi SYN-ACK")
                return (ConnHSType.TYP, datagram)
        elif datagram.get_packet_number() == self.get_package_number():
            logging.debug("Recibo un ACK en HS")
            return (ConnHSType.ACK, None)
        return self.send_SYNACK()
        
    def file_handshake(self, data = None):
        logging.warning("Comienza el File Handshake")  
        datagram = data if data is not None else self.recv_parse()
        if not datagram.is_TYP():
            logging.debug("Paquete recibido no es TYP")
            return None
        should_accept = self.should_accept(datagram)
        if not should_accept:
            logging.debug("No acepto el TYP")
            return None
        return self.accept(datagram)
        
    def should_accept(self, datagram: 'FIUBADatagram'):
        if datagram.protocol_type() == CommandType.UPLOAD:
            return self.should_accept_upload(datagram.get_data())
        if datagram.protocol_type() == CommandType.DOWNLOAD:
            return self.should_accept_download(datagram.get_data())
        return False
        
    def should_accept_upload(self, data_bytes: bytes | None) -> bool:
        if data_bytes is None:
            logging.debug("No envian informacion. No acepto")
            return False
        self.parse_upload(data_bytes) # <filename>\r\n<filesize>

        file_already_exists = self.server.exists_filename(self.file_name)
        file_size_correct = self.server.check_filesize(self.file_size)
        return not file_already_exists and file_size_correct
    
    def parse_upload(self, data_bytes: bytes | None):
        if data_bytes is None: return
        decoded = data_bytes.decode('utf-8')

        splitted = decoded.split("\r\n");
        if len(splitted) != 2: 
            logging.fatal(f"Datos recibidos en upload: {splitted}")
            return

        self.file_name = splitted[0]
        self.file_size = int(splitted[1])

    def should_accept_download(self, data_bytes: bytes | None) -> bool:
        if data_bytes is None:
            return False
        self.set_filename(data_bytes)
        logging.debug(f"Quieren descargar {self.file_name}")
        
        server_has_file = self.server.exists_filename(self.file_name)
        
        return server_has_file

    def accept(self, datagram: 'FIUBADatagram'):
        if datagram.protocol_type() == CommandType.UPLOAD:
            return self.accept_upload()
        if datagram.protocol_type() == CommandType.DOWNLOAD:
            return self.accept_download() 

    def accept_upload(self):
        logging.debug("Acepto UPLOAD. Mando UPLOAD-ACK")
        self.socket.send(self.get_UPLOADACK())
        return self.expect_data_transfer()

    def expect_data_transfer(self):
        logging.debug("Esperando data del archivo")
        datagram = self.recv_parse()
        if datagram.is_TYP():
            logging.debug("Recibi TYP devuelta, empiezo circuito de aceptacion otra vez")
            return self.file_handshake(datagram)
        return CommandType.UPLOAD, datagram

    def accept_download(self):
        logging.debug("Acepto DOWNLOAD. Mando DOWNLOAD-ACK")
        self.file_size = self.get_filesize(str(self.file_name))
        self.socket.send(self.get_DOWNLOADACK(self.file_size))
        return self.expect_DOWNLOADACK()

    def expect_DOWNLOADACK(self):
        datagram = FIUBADatagram(self.socket.recv())
        if not datagram.is_ACK() and datagram.is_TYP():
            # Solo es TYP. Es decir, cliente quiere empezar desde 0 el HS
            logging.debug("Se perdio el DOWNLOAD-ACK, re-check todo")
            return self.file_handshake(datagram)
        elif datagram.is_TYP() and datagram.protocol_type() == CommandType.DOWNLOAD:
            logging.debug("No se perdio DOWNLOAD-ACK")
            return (CommandType.DOWNLOAD, datagram)

    def execute_transfer(self, result: tuple['CommandType', 'FIUBADatagram']):
        cmdtype, first_packet = result
        match cmdtype:
            case CommandType.UPLOAD:
                logging.info("Empezando con UPLOAD")
                Receiver(
                    self.server.get_path(self.file_name), 
                    self.file_size, 
                    self.socket, 
                    self.update_package_number, 
                    self.get_package_number).download(first_packet = first_packet)
            case CommandType.DOWNLOAD:
                logging.info("Empezando con DOWNLOAD")
                Sender(
                    self.server.get_path(self.file_name), 
                    self.socket, 
                    self.update_package_number, 
                    self.get_package_number).upload()
    
    def destroy_conn(self):
        logging.debug("Cerrando conexion")
        self.socket.close()
    
    def close(self):
        self.send_FIN()
        self.destroy_conn()

    def send_FIN(self):
        logging.debug("Envio FIN")
        self.socket.send(self.get_FIN())
        self.expect_ACKFIN()

    def expect_ACKFIN(self):
        try:
            logging.debug("Espero ACK-FIN")
            datagram = self.recv_parse()
            if not (datagram.is_ACK() and datagram.is_FIN() and datagram.get_packet_number() == self.get_package_number()):
                self.send_FIN()
            logging.debug("Recibido ACK-FIN")
        except Empty:
            self.send_FIN()
    
    def set_filename(self, data: bytes | None):
        if data is None: return
        self.file_name = data.decode('utf-8')
    
    def get_filesize(self, file_name: str):
        return self.server.get_file_size(file_name)

    def get_FIN(self):
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_FIN(True).build()
    
    def get_SYNACK(self):
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_SYN(True).set_ACK(True).build()
    
    def get_UPLOADACK(self):
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_TYP(CommandType.UPLOAD).set_ACK(True).build()

    def get_DOWNLOADACK(self, file_size):
        bytes_file_size = str(file_size).encode('utf-8')
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_TYP(CommandType.DOWNLOAD).set_ACK(True).set_data(bytes_file_size).build()
    
    def recv_parse_timeout(self) -> 'FIUBADatagram':
        self.socket.settimeout(1)
        result = FIUBADatagram(self.socket.recv())
        self.socket.settimeout(None)
        return result    
    
    def recv_parse(self) -> 'FIUBADatagram':
        return FIUBADatagram(self.socket.recv())
