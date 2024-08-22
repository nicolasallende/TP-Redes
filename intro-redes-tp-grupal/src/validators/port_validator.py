MIN_PORT = 1024
MAX_PORT = 2**16

def port(astring: str) -> int:
    port = int(astring, base=10)
    if port < MIN_PORT or port > MAX_PORT:
        raise ValueError('Invalid port number; must be in (1024,65536]')
    return port