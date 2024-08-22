import os

def directory(astring: str) -> str:
    if not os.path.exists(astring) or not os.path.isdir(astring):
        raise ValueError("Invalid directory; does not exists or is not directory")
    return astring