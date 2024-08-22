import argparse
import logging
from __logging.init import init_logging
from fiubaftp_vals.types import AppType

def __process_common_args(args: 'argparse.Namespace', app_type: AppType):
    init_logging(logging.DEBUG if args.verbose else logging.WARN, app_type.value)

def process_args(parser: 'argparse.ArgumentParser', app_type: AppType) -> argparse.Namespace:
    args = parser.parse_args();
    __process_common_args(args, app_type)
    return args