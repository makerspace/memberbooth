#!/usr/bin/env python3.7

from src.backend import makeradmin
from src.test import makeradmin_mock
from src.util.logger import init_logger, get_logger
from src.util.key_reader import EM4100_KeyReader
import argparse
import config
from src.gui.states import Application
import sys

init_logger()
logger = get_logger()
start_command = " ".join(sys.argv)

def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="Makeradmin token")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin backend")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")
    parser.add_argument("--development", action="store_true", help="Mock events")

    ns = parser.parse_args()
    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer
    config.development = ns.development

    if ns.no_backend:
        makeradmin_client = makeradmin_mock.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    else:
        makeradmin_client = makeradmin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    logged_in = makeradmin_client.is_logged_in()
    logger.info(f"Logged in: {logged_in}")
    if not logged_in:
        logger.error("The makeradmin client is not logged in")
        sys.exit(-1)

    key_reader = EM4100_KeyReader.get_reader()

    app = Application(makeradmin_client, key_reader)
    app.run()


if __name__=="__main__":
    main()
