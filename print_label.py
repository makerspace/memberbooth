#!/usr/bin/env python3.7

import argparse

from src import sms_label_creator
from src import sms_label_printer

NAME_KEY = 'name'
MEMBER_NUMBER_KEY = 'member_number'

def main():

    parser = argparse.ArgumentParser(description='Print label for project box')

    parser.add_argument(MEMBER_NUMBER_KEY,
                        type=int,
                        help='The member number of the owner of the project box')

    parser.add_argument(f'--{NAME_KEY}',
                        type=str,
                        help='The name of the owner of the project box')

    args = vars(parser.parse_args())

    label = sms_label_creator.create_box_label(args[MEMBER_NUMBER_KEY], args[NAME_KEY])
    sms_label_printer.print_label(label)

if __name__== "__main__":
    main()
