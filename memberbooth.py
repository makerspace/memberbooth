#!/usr/bin/env python3.7

from src.util.logger import init_logger, get_logger
from src.util.key_reader import EM4100, Aptus, Keyboard, NoReaderFound
from src.util.slack_client import SlackClient
import argparse
import config
from src.gui.states import Application
import sys
import traceback

init_logger("memberbooth")
logger = get_logger()
slack_client = SlackClient()
start_command = " ".join(sys.argv)

INPUT_EM4100 = "EM4100"
INPUT_APTUS  = "Aptus-reader"
INPUT_KEYBOARD = "Keyboard"

def main():
    logger.info(f"Starting {sys.argv[0]} as \n\t{start_command}")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-t", "--token_path", help="Path to Makeradmin token.", default=config.token_path)
    group.add_argument("--development", action="store_true", help="Mock events")
    parser.add_argument("-u", "--maker-admin-base-url",
                        default=config.maker_admin_base_url,
                        help="Base url of maker admin backend")
    parser.add_argument("--no-backend", action="store_true", help="Mock backend (fake requests)")
    parser.add_argument("--no-printer", action="store_true", help="Mock label printer (save label to file instead)")
    parser.add_argument("--input-method", choices=(INPUT_EM4100, INPUT_APTUS, INPUT_KEYBOARD), default=INPUT_EM4100, help="The method to input the key")

    parser.add_argument("--slack_token_path", help="Path to Slack token.", default=config.slack_token_path)
    parser.add_argument("--slack_channel_id", help="Channel id for Slack channel", default=config.slack_log_channel_id)

    ns = parser.parse_args()

    config.no_backend = ns.no_backend
    config.no_printer = ns.no_printer
    config.development = ns.development
    config.token_path = ns.token_path
    config.slack_token_path = ns.slack_token_path
    config.slack_log_channel_id = ns.slack_channel_id
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

    slack_client.post_message_alert("Application was restarted!")

    app = Application(key_reader)
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
