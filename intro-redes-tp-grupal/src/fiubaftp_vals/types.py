from enum import Enum

class AppType(Enum):
    SERVER = 'start-server'
    UPLOAD = 'upload'
    DOWNLOAD = 'download'

class CommandType(Enum):
    UPLOAD = 8
    DOWNLOAD = 16

