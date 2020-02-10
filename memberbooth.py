#!/usr/bin/env python3.7

from src.util.logger import init_logger, get_logger
from src.util.key_reader import EM4100, Aptus, Keyboard, NoReaderFound
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

INPUT_EM4100 = "EM4100"
INPUT_APTUS  = "Aptus-reader"
INPUT_KEYBOARD = "Keyboard"

def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")
    development_override_action = parser_util.DevelopmentOverrideActionFactory([
        ("maker_admin_base_url", "http://localhost:8010"),
        ("printer", False),
        ("input_method", INPUT_KEYBOARD),
        ("backend", False)])
    boolean_use_action = parser_util.BooleanOptionalActionFactory("use", "no")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--token_path", help="Path to Makeradmin token.", default=config.token_path)
    group.add_argument("--development", action=development_override_action, help="Mock events. Add common development flags.")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--backend", action=boolean_use_action, default=True, help="Whether to use real backend or fake requests")
    parser.add_argument("--printer", action=boolean_use_action, default=True, help="Whether to use real label printer or save label to file instead")
    parser.add_argument("--input-method", choices=(INPUT_EM4100, INPUT_APTUS, INPUT_KEYBOARD), default=INPUT_EM4100, help="The method to input the key")

    parser.add_argument("--no-slack", action="store_true", help="Mock slack API (fake requests)")
    parser.add_argument("--slack-token-path", help="Path to Slack token.", default=config.slack_token_path)
    parser.add_argument("--slack-channel-id", help="Channel id for Slack channel")

    ns = parser.parse_args()

    config.no_backend = not ns.backend
    config.no_printer = not ns.printer
    config.development = ns.development
    config.token_path = ns.token_path
    config.maker_admin_base_url = ns.maker_admin_base_url

    if ns.input_method == INPUT_EM4100:
        try:
            key_reader = EM4100.get_reader()
        except NoReaderFound as e:
            logger.error("No EM4100 tag reader is connected. Connect one and try again.")
            sys.exit(-1)
    elif ns.input_method == INPUT_APTUS:
        key_reader = Aptus.get_reader()
    elif ns.input_method == INPUT_KEYBOARD:
        key_reader = Keyboard.get_reader()
    else:
        logger.error(f"Invalid input method: {ns.input_method}")
        sys.exit(-1)

    if ns.no_slack:
        slack_client = MockSlackClient(token_path=ns.slack_token_path, channel_id=ns.slack_channel_id)
    else:
        slack_client = SlackClient(token_path=ns.slack_token_path, channel_id=ns.slack_channel_id)

    app = Application(key_reader, slack_client)
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
