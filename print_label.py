#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
from colors import color
from src.backend.label_data import BoxLabel, MeetupNameTag, NameTag, Printer3DLabel, TemporaryStorageLabel, WarningLabel
from src.label import creator as label_creator
from src.label import printer as label_printer
from src.backend import makeradmin
from src.backend.member import Member
from src.backend.member import NoMatchingMemberNumber
from time import time
from src.util.logger import init_logger, get_logger
from src.test import makeradmin_mock
import config

init_logger("print_label")
logger = get_logger()


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("--type", choices=["box", "temp", "3d", "warning", "meetup"], default="name")
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
    
    parser.add_argument('--description', type=str, help='Description to put on temporary storage labels', default=None)

    ns = parser.parse_args()
    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer
    config.makeradmin_token_filename = ns.token_path
    config.maker_admin_base_url = ns.maker_admin_base_url

    if ns.no_backend:
        makeradmin_client: makeradmin_mock.MakerAdminClient | makeradmin.MakerAdminClient = makeradmin_mock.MakerAdminClient()
    else:
        makeradmin_client = makeradmin.MakerAdminClient(base_url=config.maker_admin_base_url,
                                                        token_path=config.makeradmin_token_filename)
    while not makeradmin_client.is_logged_in():
        logger.warning("The makeradmin client is not logged in")
        makeradmin_client.login()

    for member_number in ns.member_numbers:
        try:
            member = Member.from_member_number(makeradmin_client, member_number)
        except NoMatchingMemberNumber:
            logger.error(f"Member number {member_number} did not match any known member")
        else:

            match ns.type:
                case "box":
                    label_data = BoxLabel.from_member(member)
                case "temp":
                    if ns.description is None:
                        logger.error("You must provide a description for temporary storage labels using --description")
                        continue
                    label_data = TemporaryStorageLabel.from_member(member,
                                                                   description=ns.description,
                                                                   expires_at=(datetime.now() + timedelta(days=int(label_creator.TEMP_STORAGE_LENGTH))).date()
                                                                   )
                case "3d":
                    label_data = Printer3DLabel.from_member(member)
                case "name":
                    label_data = NameTag.from_member(member)
                case "meetup":
                    label_data = MeetupNameTag.from_member(member)
                case "warning":
                    maybe_y = input(color(
                        "Make sure that the yellow label printer paper roll is currently in use.", bg='yellow', fg='black')
                        + "\nSee https://wiki.makerspace.se/Memberbooth for info on how to change the printer paper.\n"
                        "         Type 'y' to continue, or anything else to exit. ")
                    if maybe_y.lower() != 'y':
                        print("Exiting")
                        return

                    # TODO: Use logged in member
                    label_data = WarningLabel.from_member(member, description=ns.description, expires_at=(datetime.now() + timedelta(days=int(label_creator.TEMP_WARNING_STORAGE_LENGTH))).date())

            uploaded_label = makeradmin_client.post_label(label_data)
            label = label_creator.create_label(uploaded_label)

            if ns.no_printer:
                file_name = f'box_label_{member.member_number}_{str(int(time()))}.png'
                logger.info(
                    f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
                print(f"Saving box label to {file_name}")
                label.save(file_name)
                label.show()
            else:
                label_printer.print_label(label.label)


if __name__ == "__main__":
    main()
