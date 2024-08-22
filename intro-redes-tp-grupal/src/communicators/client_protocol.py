from communicators.protocol import Protocol
from datagrams.fiuba_datagram import FIUBADatagram
from datagrams.fiuba_datagram_builder import FIUBADatagramBuilder
from fiubaftp_vals.types import CommandType
import logging
from communicators.sender import Sender
from communicators.receiver import Receiver

class ClientProtocol(Protocol):

    def __init__(self, client, connection):
        super().__init__()
        self.client = client
        self.socket = connection
        self.fin_received = False

    def exec(self):
        if self.connection_handshake():
            logging.debug("Termino CONN HS. Empiezo FILE HS")
            file_hs_result = self.file_handshake(self.client.get_type())
            if file_hs_result:
                logging.debug("Termino FILE HS. Empiezo transferencia")
                match self.client.get_type():
                    case CommandType.UPLOAD:
                        self.execute_transfer(CommandType.UPLOAD)
                    case CommandType.DOWNLOAD:
                        self.execute_transfer(self.client.get_type(), file_hs_result) # type: ignore

        self.close()

    def connection_handshake(self):
        logging.warning("Comienza el Handshake")  
        self.send_SYN()
        return self.expect_SYNACK()

    def send_SYN(self):
        logging.debug("Mando SYN")
        self.send(self.get_SYN())

    def expect_SYNACK(self):
        try:
            logging.debug("Espero SYN-ACK")
            datagram = self.recvtimeout()
            if datagram.is_FIN():
                logging.debug("Recibo FIN")
                self.fin_received = True
                return False
            
            if not (datagram.is_SYN() and datagram.is_ACK()):
                logging.debug("SYN-ACK perdido")
                self.connection_handshake()

            self.set_package_number(datagram.get_packet_number())
            self.send_SYNACK()
            return True
        except TimeoutError:
            return self.connection_handshake()

    def send_SYNACK(self):
        logging.debug("Mando SYN-ACK")
        self.send(self.get_SYNACK())
    
    def file_handshake(self, connection_type: CommandType):
        logging.warning("Comienza el File Handshake")  
        match connection_type:
            case CommandType.UPLOAD:
                return self.file_handshake_upload()
            case CommandType.DOWNLOAD:
                return self.file_handshake_download()
                
    def file_handshake_upload(self):
        logging.debug("Comienza el Upload HS")
        self.send_UPLOAD()
        return self.expect_UPLOADACK()

    def send_UPLOAD(self):
        logging.debug("Mando UPLOAD")
        file_data = f"{self.client.get_file_name()}\r\n{self.client.get_file_size()}"
        upload = self.get_UPLOAD(file_data)
        self.send(upload)

    def expect_UPLOADACK(self):
        try:
            logging.debug("Espero UPLOAD-ACK")
            datagram = self.recvtimeout()
            if datagram.is_FIN():
                logging.debug("Recibi FIN")  
                self.fin_received = True
                return False
            if not (datagram.is_TYP() and datagram.protocol_type() == CommandType.UPLOAD):
                logging.debug("UPLOAD-ACK no receibido")
                self.file_handshake_upload()
            logging.debug("UPLOAD-ACK receibido")
            return True
        except TimeoutError:
            logging.warning("Se perdio paquete de UPLOAD o UPLOAD-ACK del Servidor")
            return self.file_handshake_upload()

    def file_handshake_download(self):
        logging.debug("Comienza el DOWNLOAD-HS")
        self.send_DOWNLOAD()
        if not self.expect_DOWNLOADACK():
            logging.debug("El Servidor no quiere transferir el archivo")
            return False
        self.send_DOWNLOADACK()
        return self.expect_file_data()

    def send_DOWNLOAD(self):
        logging.debug("Mando DOWNLOAD")
        file_data = f"{self.client.get_file_name()}"
        packet = self.get_DOWNLOAD(file_data)
        self.send(packet)

    def expect_DOWNLOADACK(self):
        try:
            datagram = self.recvtimeout()
            if datagram.is_FIN():
                logging.warning("EL Servidor no tiene informacion")
                self.fin_received = True
                return False
            if not (datagram.is_ACK() and datagram.is_TYP() and datagram.protocol_type() == CommandType.DOWNLOAD):
                logging.debug("DOWNLOAD-ACK no recibido")
                return self.file_handshake_download()
            logging.debug("DOWNLOAD-ACK recibido")
            self.parse_file_size(datagram.get_data())
            return True
        except TimeoutError:
            logging.warning("Se perdio paquete de DOWNLOAD o DOWNLOAD-ACK del Servidor")
            return self.file_handshake_download()

    def send_DOWNLOADACK(self):
        file_data = f"{self.client.get_file_name()}\r\n{self.client.get_file_size()}"
        packet = self.get_DOWNLOADACK(file_data)
        self.send(packet)

    def expect_file_data(self):
        try:
            datagram = self.recvtimeout()
            return datagram
        except TimeoutError:
            logging.warning("Se perdio paquete de DOWNLOAD-ACK del cliente. Reenviando")
            self.send_DOWNLOADACK()
            return self.expect_file_data()
        
    def set_FIN_received(self):
        self.fin_received = True

    def stop_receiving(self, datagram: 'FIUBADatagram'):
        if datagram.is_FIN():
            self.fin_received = True
            return True
        return False

    def execute_transfer(self, cmdtype: CommandType, first_packet: FIUBADatagram | None = None):
        logging.warning("Comienza la transferencia del archivo")  
        match cmdtype:
            case CommandType.UPLOAD:
                logging.warning("El cliente es el sender")
                logging.debug("UPLOAD comienza")
                Sender(self.client.get_file_path(), 
                       self.socket,
                       self.update_package_number, 
                       self.get_package_number,
                       on_FIN = self.set_FIN_received).upload()
            case CommandType.DOWNLOAD:
                logging.warning("El cliente es el receiver")
                logging.debug("DOWNLOAD comienza")
                Receiver(
                    self.client.get_file_path(), 
                    self.client.get_file_size(), 
                    self.socket, 
                    self.update_package_number, 
                    self.get_package_number).download(keep_confirming_until=(True, self.stop_receiving),first_packet = first_packet)

    def send(self, data: bytes):
        self.socket.send(data)

    def recvtimeout(self, timeout: float | None = 1):
        self.socket.settimeout(timeout)
        datagram = FIUBADatagram(self.socket.recv())
        self.socket.settimeout(None)
        return datagram
    
    def recv(self):
        return FIUBADatagram(self.socket.recv())

    def close(self):
        if self.fin_received:
            logging.info("FIN recibido anteriormente")
            return self.send_ACKFIN()
        return self.expect_FIN(None)
    
    def send_ACKFIN(self):
        logging.debug("Mando ACK-FIN")
        self.send(self.get_ACKFIN())
        try:
            self.expect_FIN(10)
        except TimeoutError:
            logging.info("Conexion con el servidor cerrada")
            return
        
    def parse_file_size(self, data: bytes | None):
        if data is None: return
        decoded = int(data.decode('utf-8'))
        self.client.set_file_size(decoded)
        
    def expect_FIN(self, timeout: float | None = None):
        logging.debug(f"Esperando FIN. Timeout {timeout}")
        datagram = self.recvtimeout(timeout)
        if datagram.is_FIN():
            return self.send_ACKFIN()
        return self.expect_FIN()
    
    def get_SYN(self):
        return FIUBADatagramBuilder().set_SYN(True).build()
    
    def get_SYNACK(self):
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_ACK(True).build()

    def get_UPLOAD(self, filedata: str):
        str_bytes = bytes(filedata, 'utf-8')
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_TYP(CommandType.UPLOAD).set_data(str_bytes).build()

    def get_DOWNLOAD(self, filedata: str):
        str_bytes = bytes(filedata, 'utf-8')
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_TYP(CommandType.DOWNLOAD).set_data(str_bytes).build()

    def get_DOWNLOADACK(self, filedata: str):
        str_bytes = bytes(filedata, 'utf-8')
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_TYP(CommandType.DOWNLOAD).set_ACK(True).set_data(str_bytes).build()

    def get_ACKFIN(self):
        return FIUBADatagramBuilder().set_packet_nbr(self.get_package_number()).set_FIN(True).set_ACK(True).build()