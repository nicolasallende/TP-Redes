import logging

def init_logging(level, user: str):
    logging.basicConfig(
        level=level,
        format=f'[{user} %(asctime)s.%(msecs)03d %(levelname)s] - %(message)s',
        datefmt='%H:%M:%S'
    )