import ipaddress
from ipaddress import IPv4Address, IPv6Address

def ip(astring: str) -> 'IPv4Address | IPv6Address':
    return ipaddress.ip_address(astring)