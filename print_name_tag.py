#!/usr/bin/env python3

import argparse
from src.backend import makeradmin
from src.test import makeradmin_mock
from src.backend.member import Member
from src.backend.member import NoMatchingMemberNumber
from src.label import creator as label_creator
from src.label import printer as label_printer
from time import time
from src.util.logger import init_logger, get_logger
import config
import sys

init_logger("print_label")
logger = get_logger()
start_command = " ".join(sys.argv)


def print_label(label, no_printer: bool = False):
    if no_printer:
        file_name = f'Name_tag_{str(int(time()))}.png'
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
    parser.add_argument("-t", "--token_path", help="Path to Makeradmin token.", default=config.makeradmin_token_filename)
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")
    parser.add_argument("member_number", type=int, help="The member number of the member you want to print the tag for")

    args = parser.parse_args()
    config.no_backend = args.no_backend
    config.no_printer = args.no_printer
    config.token_path = args.token_path
    config.maker_admin_base_url = args.maker_admin_base_url

    if args.no_backend:
        makeradmin_client = makeradmin_mock.MakerAdminClient()
    else:
        makeradmin_client = makeradmin.MakerAdminClient(base_url=config.maker_admin_base_url,
                                                        token_path=config.token_path)
    while not makeradmin_client.is_logged_in():
        logger.warning("The makeradmin client is not logged in")
        makeradmin_client.login()

    try:
        member = Member.from_member_number(makeradmin_client, args.member_number)
        label = label_creator.create_name_tag(member.member_number, member.get_name(), member.membership.end_date)
        print_label(label, config.no_printer)
    except NoMatchingMemberNumber:
        logger.error(f"Member number {args.member_number} did not match any known member")


if __name__ == "__main__":
    main()
