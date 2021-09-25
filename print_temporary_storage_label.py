#!/usr/bin/env python3

import argparse
from src.label import creator as label_creator
from src.label import printer as label_printer
from time import time
from src.util.logger import init_logger, get_logger
from src.backend.member import Member
from src.backend import makeradmin
from src.test import makeradmin_mock
import config
import sys

init_logger("print_temporary_storage_label")
logger = get_logger()
start_command = " ".join(sys.argv)


def print_label(label, no_printer: bool = False):
    if no_printer:
        file_name = f'warning_label_{str(int(time()))}.png'
        logger.info(
            f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
        print(f"Saving warning label to {file_name}")
        label.save(file_name)
        label.show()
    else:
        label_printer.print_label(label.label)


def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")
    parser.add_argument("--no-backend", action="store_true", help="Do not use the makeradmin backend")
    parser.add_argument("member_id", type=int, help="The member number")
    parser.add_argument("description", help="The description of the temporary storage label")

    args = parser.parse_args()
    config.no_printer = args.no_printer

    if args.no_backend:
        makeradmin_client = makeradmin_mock.MakerAdminClient()
    else:
        makeradmin_client = makeradmin.MakerAdminClient(base_url=config.maker_admin_base_url,
                                                        token_path=config.token_path)
    while not makeradmin_client.is_logged_in():
        logger.warning("The makeradmin client is not logged in")
        makeradmin_client.login()

    member = Member.from_member_number(makeradmin_client, args.member_id)
    label = label_creator.create_temporary_storage_label(args.member_id, member.get_name(), args.description)
    print_label(label, args.no_printer)


if __name__ == "__main__":
    main()
