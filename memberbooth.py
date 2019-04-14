#!/usr/bin/env python3.7

from src import maker_admin
from src.test import maker_admin_mock
import argparse
import config
from src.application_states import Application

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="Makeradmin token")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default='https://api.makeradmin.se',
                        help="Base url of maker admin (for login and fetching of member info).")
    parser.add_argument("--debug", action="store_true", help="Do not send requests to the backend")
    parser.add_argument("--no_printing", action="store_true", help="Image is sent to label printer, instead the image is saved to working directory")

    config.ns = parser.parse_args()

    if config.ns.debug:
        makeradmin_client = maker_admin_mock.MakerAdminClient(base_url=config.ns.maker_admin_base_url, token=config.ns.token)
    else:
        makeradmin_client = maker_admin.MakerAdminClient(base_url=config.ns.maker_admin_base_url, token=config.ns.token)
    logged_in = makeradmin_client.is_logged_in()
    print("Logged in: ", logged_in)
    if not logged_in:
        return

    app = Application(makeradmin_client)
    app.run()


if __name__=="__main__":
    main()
