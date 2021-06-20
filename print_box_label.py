#!/usr/bin/env python3

import argparse

from src.label import creator as label_creator
from src.label import printer as label_printer
from src.backend import makeradmin
from src.backend.member import Member
from src.backend.member import NoMatchingMemberNumber
from time import time
from src.util.logger import init_logger, get_logger
import config
import sys

init_logger("print_label")
logger = get_logger()
start_command = " ".join(sys.argv)


def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-t", "--token_path", help="Path to Makeradmin token.", default=config.makeradmin_token_filename)
    group.add_argument("--development", action="store_true", help="Mock events")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")

    parser.add_argument('member_numbers',
                        type=int,
                        nargs='+',
                        help='The member number(s) of the member(s) you want to print a label for')

    ns = parser.parse_args()
    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer
    config.token_path = ns.token_path
    config.maker_admin_base_url = ns.maker_admin_base_url

    makeradmin_client = makeradmin.MakerAdminClient(base_url=config.maker_admin_base_url,
                                                    token_path=config.token_path)
    while not makeradmin_client.is_logged_in():
        logger.warning("The makeradmin client is not logged in")
        makeradmin_client.login()

    for member_number in ns.member_numbers:
        try:
            member = Member.from_member_number(makeradmin_client, member_number)
        except NoMatchingMemberNumber:
            logger.error(f"Member number {member_number} did not match any known member")
        else:
            label = label_creator.create_box_label(member.member_number, member.get_name())

            if ns.no_printer:
                file_name = f'{member.member_number}_{str(int(time()))}.png'
                logger.info(
                    f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
                label.save(file_name)
            else:
                label_printer.print_label(label)


if __name__ == "__main__":
    main()
