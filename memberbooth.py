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
                        help="Base url of maker admin backend")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")

    ns = parser.parse_args()
    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer

    if ns.no_backend:
        makeradmin_client = maker_admin_mock.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    else:
        makeradmin_client = maker_admin.MakerAdminClient(base_url=ns.maker_admin_base_url, token=ns.token)
    logged_in = makeradmin_client.is_logged_in()
    print("Logged in: ", logged_in)
    if not logged_in:
        return

    app = Application(makeradmin_client)
    app.run()


if __name__=="__main__":
    main()
