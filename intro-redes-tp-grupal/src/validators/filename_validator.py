import re

REGEX_PATTERN = r'^[^<>:"/\\|?*\x00-\x1F]*$'

def filename(astring: str) -> str:
    if not re.match(REGEX_PATTERN, astring):
        raise ValueError("Invalid filename")
    return astring