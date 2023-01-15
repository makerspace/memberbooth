#!/usr/bin/env python3

import config
import argparse
import sys
from src.util.logger import init_logger, get_logger
import src.util.parser as parser_util
from src.backend.makeradmin import MakerAdminClient
from src.util.slack_client import SlackClient

init_logger("login")
logger = get_logger()
start_command = " ".join(sys.argv)


def main():
    boolean_login_action = parser_util.BooleanOptionalActionFactory("login", "skip")

    parser = argparse.ArgumentParser(description="Logs into services that are required for running the memberbooth")

    makeradmin_group = parser.add_argument_group("Makeradmin")
    makeradmin_group.add_argument("-u", "--maker-admin-base-url",
                                  default=config.maker_admin_base_url,
                                  help="Base url of maker admin backend")
    makeradmin_group.add_argument("--makeradmin", action=boolean_login_action, default=True,
                                  help="Whether to login Makeradmin or skip")

    slack_group = parser.add_argument_group("Slack")
    slack_group.add_argument("--slack", action=boolean_login_action, default=True,
                             help="Whether to login Slack or skip")
    slack_group.add_argument("--slack-channel-id", help="Channel id for Slack channel")

    ns = parser.parse_args()

    services = []
    if ns.makeradmin:
        services.append("makeradmin")
    if ns.slack:
        services.append("slack")

    for s in services:
        if s == "slack":
            token_path = config.slack_token_filename
            if ns.slack_channel_id is None:
                logger.error("The Slack channel ID must be specified")
                print("Skipping Slack login")
                continue
            client = SlackClient(token_path=token_path, channel_id=ns.slack_channel_id)
        elif s == "makeradmin":
            token_path = config.makeradmin_token_filename
            client = MakerAdminClient(base_url=ns.maker_admin_base_url, token_path=token_path)

        try:
            while not client.configured:
                client.login()
        except EOFError:
            print(f"\nSkipping login of {s}")
            continue
        print(f"Logged in with {s} token")

        logger.info(f"Creating token file '{token_path}'")
        with open(token_path, "w") as f:
            f.write(client.token)

    print("Done")


if __name__ == "__main__":
    main()
