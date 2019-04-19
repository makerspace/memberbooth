#!/usr/bin/env python3.7

import argparse

from src import label_creator
from src import label_printer
from src import maker_admin
from src.member import Member
from logging import basicConfig, INFO
import sys
import config 

basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)

def main():

    parser = argparse.ArgumentParser(description='Print label for project box')
    parser.add_argument("token", help="Makeradmin token")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).)")
    
    parser.add_argument("--debug", action="store_true", help="Do not send requests to the backend")
    parser.add_argument("--no_printing", action="store_true", help="Image is sent to label printer, instead the image is saved to working directory")
    
    parser.add_argument('member_number',
                        type=str,
                        help='The member number of the member you want to print a label for')

    ns = parser.parse_args()
    config.debug = ns.debug
    config.no_printing = ns.no_printing
    
    makeradmin_client = maker_admin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)

    logged_in = makeradmin_client.is_logged_in()
    print("Logged in: ", logged_in)
    if not logged_in:
        return

    member = Member.from_member_number(makeradmin_client, ns.member_number)

    label = label_creator.create_box_label(member.member_number, member.get_name())
    
    if ns.no_printing:
        file_name = f'{member.member_number}_{str(int(time()))}.png'
        print(f'Program run with --no_printing, storing image to {file_name} instead of printing it.')
        label.save(file_name)
        return
    
    label_printer.print_label(label)

if __name__== "__main__":
    main()
