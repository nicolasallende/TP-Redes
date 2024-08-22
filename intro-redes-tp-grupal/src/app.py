from cmd_args.init import define_args
from cmd_args.process import process_args
from server import Server
from client import Client
from fiubaftp_vals.types import CommandType

from fiubaftp_vals.types import AppType

def main(app_type: AppType):
    args = process_args(define_args(app_type), app_type)
    match app_type:
        case AppType.UPLOAD:
            Client(args, type= CommandType.UPLOAD).run()
        case AppType.DOWNLOAD:
            Client(args, type= CommandType.DOWNLOAD).run()
        case AppType.SERVER:
            Server(args).run()

if __name__ == '__main__':
    main(AppType.SERVER)