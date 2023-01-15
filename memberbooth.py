#!/usr/bin/env python3

from src.util.logger import init_logger, get_logger
from src.backend.makeradmin import MakerAdminClient
from src.test.makeradmin_mock import MakerAdminClient as MockedMakerAdminClient
from src.util.slack_client import SlackClient
from src.test.slack_client_mock import MockSlackClient
import src.util.parser as parser_util
import argparse
import config
from src.gui.states import Application
import sys
import traceback

init_logger("memberbooth")
logger = get_logger()
start_command = " ".join(sys.argv)


def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")
    development_override_action = parser_util.DevelopmentOverrideActionFactory([
        ("maker_admin_base_url", "http://localhost:8010"),
        ("printer", False),
        ("backend", False)])
    boolean_use_action = parser_util.BooleanOptionalActionFactory("use", "no")

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument("--development", action=development_override_action,
                        help="Mock events. Add common development flags.")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--backend", action=boolean_use_action, default=True,
                        help="Whether to use real backend or fake requests")
    parser.add_argument("--slack", action=boolean_use_action, default=True,
                        help="Whether to use slack backend or pass to logger instead")
    parser.add_argument("--printer", action=boolean_use_action, default=True,
                        help="Whether to use real label printer or save label to file instead")

    parser.add_argument("--slack-channel-id", help="Channel id for Slack channel")

    ns = parser.parse_args()

    config.no_backend = no_backend = not ns.backend
    config.no_printer = not ns.printer
    config.development = ns.development
    no_slack = not ns.slack

    if no_backend:
        makeradmin_client = MockedMakerAdminClient(base_url=config.maker_admin_base_url,
                                                   token_path=config.makeradmin_token_filename)
    else:
        makeradmin_client = MakerAdminClient(base_url=ns.maker_admin_base_url, token_path=config.makeradmin_token_filename)

    if no_slack:
        slack_client = MockSlackClient(token_path=config.slack_token_filename, channel_id=ns.slack_channel_id)
    elif ns.slack_channel_id is None:
        print("The Slack channel ID must be specified to use slack logging. Skipping Slack login")
        slack_client = MockSlackClient(token_path=config.slack_token_filename, channel_id=ns.slack_channel_id)
    else:
        slack_client = SlackClient(token_path=config.slack_token_filename, channel_id=ns.slack_channel_id, timeout=config.slack_timeout)

    app = Application(makeradmin_client, slack_client)
    try:
        app.run()
    except KeyboardInterrupt:
        app.master.destroy()
    except Exception:
        logger.error(traceback.format_exc())
    finally:
        logger.info("Exiting application")


if __name__ == "__main__":
    main()
