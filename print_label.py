#!/usr/bin/env python3

import argparse
from datetime import datetime, timedelta
from colors import color
from src.backend.label_data import BoxLabel, FireSafetyLabel, MeetupNameTag, NameTag, Printer3DLabel, RotatingStorageLabel, TemporaryStorageLabel, WarningLabel
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

def print_label(member: Member, makeradmin_client: makeradmin.MakerAdminClient | makeradmin_mock.MakerAdminClient, type: str, no_printer: bool = False, description: str | None = None) -> None:
    match type:
        case "box":
            label_data = BoxLabel.from_member(member)
        case "temp":
            if description is None:
                logger.error("You must provide a description for temporary storage labels using --description")
                return
            label_data = TemporaryStorageLabel.from_member(member,
                                                            description=description,
                                                            expires_at=(datetime.now() + timedelta(days=int(label_creator.TEMP_STORAGE_LENGTH))).date()
                                                            )
        case "fire":
            label_data = FireSafetyLabel.from_member(member, expires_at=(datetime.now() + timedelta(days=int(label_creator.TEMP_STORAGE_LENGTH))).date())
        case "3d":
            label_data = Printer3DLabel.from_member(member)
        case "name":
            label_data = NameTag.from_member(member)
        case "meetup":
            label_data = MeetupNameTag.from_member(member)
        case "rotating":
            if description is None:
                logger.error("You must provide a description for rotating storage labels using --description")
                return
            label_data = RotatingStorageLabel.from_member(member, description=description)
        case "warning":
            maybe_y = input(color(
                "Make sure that the yellow label printer paper roll is currently in use.", bg='yellow', fg='black')
                + "\nSee https://wiki.makerspace.se/Memberbooth for info on how to change the printer paper.\n"
                "         Type 'y' to continue, or anything else to exit. ")
            if maybe_y.lower() != 'y':
                print("Exiting")
                return

            # TODO: Use logged in member
            label_data = WarningLabel.from_member(member, description=description, expires_at=(datetime.now() + timedelta(days=int(label_creator.TEMP_WARNING_STORAGE_LENGTH))).date())

    uploaded_label = makeradmin_client.post_label(label_data)
    label = label_creator.create_label(uploaded_label)

    if no_printer:
        file_name = f'{member.member_number}_{type}_{str(int(time()))}.png'
        logger.info(
            f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
        print(f"Saving box label to {file_name}")
        label.save(file_name)
        label.show()
    else:
        label_printer.print_label(label.label)

def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group2 = parser.add_mutually_exclusive_group()
    parser.add_argument("--type", choices=["box", "temp", "3d", "warning", "name", "meetup", "fire", "rotating"], default="name")
    group.add_argument("-t", "--token_path", help="Path to Makeradmin token.", default=config.makeradmin_token_filename)
    group.add_argument("--development", action="store_true", help="Mock events")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")

    group2.add_argument('member_numbers',
                        type=int,
                        nargs='*',
                        help='The member number(s) of the member(s) you want to print a label for')
    group2.add_argument('--interactive', action='store_true', help='Ask before printing each label')

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

    if ns.interactive:
        while True:
            try:
                input_str = input(color("Enter member number: ", fg='orange'))
                if input_str.lower() == 'q':
                    print(color("Exiting interactive mode.", fg='yellow'))
                    exit(0)
                member_number = int(input_str)
            except ValueError:
                print(color("Invalid input. Please enter a valid member number.", fg='red'))
                continue

            try:
                member = Member.from_member_number(makeradmin_client, member_number)
            except NoMatchingMemberNumber:
                print(color(f"Member number {member_number} did not match any known member", fg='red'))
                continue

            maybe_y = input(color(f"Print {ns.type} label for", fg="orange") + color(" " + member.get_name(), style='bold') + color(f" (#{member.member_number})? (y/n) ", fg='orange'))
            if maybe_y.lower() == 'y':
                print_label(member, makeradmin_client, ns.type, ns.no_printer, ns.description)
    else:
        if not ns.member_numbers:
            print(color("No member numbers provided. Use --interactive to enter member numbers one by one, or provide member numbers as arguments.", fg='red'))

        for member_number in ns.member_numbers:
            try:
                member = Member.from_member_number(makeradmin_client, member_number)
            except NoMatchingMemberNumber:
                logger.error(f"Member number {member_number} did not match any known member")
            print_label(member, makeradmin_client, ns.type, ns.no_printer, ns.description)


if __name__ == "__main__":
    main()
