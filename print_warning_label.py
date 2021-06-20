#!/usr/bin/env python3

import argparse
from colors import color

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
        file_name = f'warning_label_{str(int(time()))}.png'
        logger.info(
            f'Program run with --no-printer, storing label image to {file_name} instead of printing it.')
        print(f"Saving warning label to {file_name}")
        label.save(file_name)
        label.show()
    else:
        label_printer.print_label(label)


def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")

    ns = parser.parse_args()
    config.no_printer = ns.no_printer

    maybe_y = input(color(
        "Make sure that the yellow label printer paper roll is currently in use.\n", fg='yellow')
        + "See https://wiki.makerspace.se/Memberbooth for info on how to change the printer paper.\n"
        "         Type 'y' to continue, or anything else to exit. ")
    if maybe_y.lower() != 'y':
        print("Exiting")
        sys.exit(0)

    while input(" * Type 'y' to print a warning label. ").lower() == 'y':
        label = label_creator.create_warning_label()
        print_label(label, ns.no_printer)


if __name__ == "__main__":
    main()
