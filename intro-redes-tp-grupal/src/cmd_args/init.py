import argparse
from fiubaftp_vals.types import AppType
from validators.dir_validator import directory
from validators.file_validator import file
from validators.filename_validator import filename
from validators.ip_validator import ip
from validators.port_validator import port

METAVAR_IP = "<IP Addr>"
METAVAR_PORT = "<Port>"
METAVAR_PATH = "<Path>"
METAVAR_FILENAME = "<Filename>"

TYPE_IP = ip
TYPE_PORT = port
TYPE_FILE = file
TYPE_DIR = directory
TYPE_FILENAME = filename

def __define_common_args(parser: 'argparse.ArgumentParser'):
    parser.add_argument("-v", "--verbose", 
                        help="Increases the output of the logging of the application. Takes precedence over -q.",
                        action="store_true")
    parser.add_argument("-q", "--quiet",
                        help="Decreases the output of the logging of the application",
                        action="store_true")

def __define_server_args(parser: 'argparse.ArgumentParser'):
    # parser.add_argument("start-server")
    parser.add_argument("-H", "--host",
                        help="service IP address",
                        action="store",
                        metavar=METAVAR_IP,
                        type= TYPE_IP,
                        required=True)
    parser.add_argument("-p", "--port",
                        help="service port",
                        action="store",
                        metavar=METAVAR_PORT,
                        type=TYPE_PORT,
                        required=True)
    parser.add_argument("-s", "--storage",
                        help="storage dir path",
                        action="store",
                        metavar=METAVAR_PATH,
                        type=TYPE_DIR,
                        required=True)

def __define_client_common_args(parser: 'argparse.ArgumentParser'):
    parser.add_argument("-H", "--host",
                        help="server IP address",
                        action="store",
                        metavar=METAVAR_IP,
                        type= TYPE_IP,
                        required=True)
    parser.add_argument("-p", "--port",
                        help="server port",
                        action="store",
                        metavar=METAVAR_PORT,
                        type=TYPE_PORT,
                        required=True)

def __define_upload_args(parser: 'argparse.ArgumentParser'):
    __define_client_common_args(parser)
    parser.add_argument("-s", "--src",
                        help="Complete path to the file that will be uploaded",
                        action="store",
                        metavar=METAVAR_PATH,
                        type=TYPE_DIR,
                        required=True)
    parser.add_argument("-n", "--name",
                        help="Name of how the file will be saved in the server",
                        action="store",
                        metavar=METAVAR_FILENAME,
                        type=TYPE_FILENAME,
                        required=True)
    
def __define_download_args(parser: 'argparse.ArgumentParser'):
    __define_client_common_args(parser)
    parser.add_argument("-d", "--dst",
                        help="Source path where the file will be saved",
                        action="store",
                        metavar=METAVAR_PATH,
                        type=TYPE_DIR,
                        required=True)
    parser.add_argument("-n", "--name",
                        help="Name of the file to download from the server",
                        action="store",
                        metavar=METAVAR_FILENAME,
                        type=TYPE_FILENAME,
                        required=True)

def define_args(app_type: AppType) -> 'argparse.ArgumentParser':
    parser = argparse.ArgumentParser()
    __define_common_args(parser)
    match app_type:
        case AppType.SERVER:
            __define_server_args(parser)
        case AppType.UPLOAD:
            __define_upload_args(parser)
        case AppType.DOWNLOAD:
            __define_download_args(parser)
            
    return parser