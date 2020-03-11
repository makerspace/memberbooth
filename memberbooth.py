#!/usr/bin/env python3.7

from src.util.logger import init_logger, get_logger
from src.util.key_reader import EM4100, Aptus, Keyboard, InputMethods, NoReaderFound
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
        ("input_method", InputMethods.KEYBOARD),
        ("backend", False)])
    boolean_use_action = parser_util.BooleanOptionalActionFactory("use", "no")

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument("--development", action=development_override_action, help="Mock events. Add common development flags.")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--backend", action=boolean_use_action, default=True, help="Whether to use real backend or fake requests")
    parser.add_argument("--slack",   action=boolean_use_action, default=True, help="Whether to use slack backend or pass to logger instead")
    parser.add_argument("--printer", action=boolean_use_action, default=True, help="Whether to use real label printer or save label to file instead")
    parser.add_argument("--input-method", choices=InputMethods, default=InputMethods.EM4100, type=InputMethods.from_string, help="The method to input the key")

    token_group = parser.add_argument_group(description="Tokens")
    token_group.add_argument("--makeradmin-token-path", "-t", help="Path to Makeradmin token", default=config.makeradmin_token_path)
    token_group.add_argument("--slack-token-path", help="Path to Slack token.", default=config.slack_token_path)
    token_group.add_argument("--slack-channel-id", help="Channel id for Slack channel")

    ns = parser.parse_args()

    config.no_backend = no_backend = not ns.backend
    config.no_printer = no_printer = not ns.printer
    config.development = ns.development
    no_slack = not ns.slack

    if ns.input_method == InputMethods.EM4100:
        key_reader_class = EM4100
    elif ns.input_method == InputMethods.APTUS:
        key_reader_class = Aptus
    elif ns.input_method == InputMethods.KEYBOARD:
        key_reader_class = Keyboard
    else:
        logger.error(f"Invalid input method: {ns.input_method}")
        sys.exit(-1)

    if no_backend:
        makeradmin_client = MockedMakerAdminClient(base_url=config.maker_admin_base_url, token_path=ns.makeradmin_token_path)
    else:
        makeradmin_client = MakerAdminClient(base_url=ns.maker_admin_base_url, token_path=ns.makeradmin_token_path)

    if no_slack:
        slack_client = MockSlackClient(token_path=ns.slack_token_path, channel_id=ns.slack_channel_id)
    else:
        slack_client = SlackClient(token_path=ns.slack_token_path, channel_id=ns.slack_channel_id)

    app = Application(key_reader_class, makeradmin_client, slack_client)
    try:
        app.run()
    except KeyboardInterrupt:
        app.master.destroy()
    except:
        logger.error(traceback.format_exc())
    finally:
        logger.info("Exiting application")

if __name__=="__main__":
    main()
