import os

def file(astring: str) -> str:
    if not os.path.exists(astring) or not os.path.isfile(astring):
        raise ValueError("Invalid file; does not exist or is not a file")
    return astring