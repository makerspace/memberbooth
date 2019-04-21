#!/usr/bin/env python3.7

import argparse

from src import label_creator
from src import label_printer
from src import maker_admin
from src.member import Member
from time import time
import config 

def main():

    parser = argparse.ArgumentParser(description='Print label for project box')
    parser.add_argument("token", help="Makeradmin token")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin backend")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")
    
    parser.add_argument('member_number',
                        type=str,
                        help='The member number of the member you want to print a label for')

    ns = parser.parse_args()
    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer
    
    makeradmin_client = maker_admin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)

    logged_in = makeradmin_client.is_logged_in()
    print("Logged in: ", logged_in)
    if not logged_in:
        return

    member = Member.from_member_number(makeradmin_client, ns.member_number)

    label = label_creator.create_box_label(member.member_number, member.get_name())
    
    if ns.no_printer:
        file_name = f'{member.member_number}_{str(int(time()))}.png'
        print(f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
        label.save(file_name)
        return
    
    label_printer.print_label(label)

if __name__== "__main__":
    main()
