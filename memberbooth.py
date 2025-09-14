#!/usr/bin/env python3

import os
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
import zipfile
import urllib.request

init_logger("memberbooth")
logger = get_logger()
start_command = " ".join(sys.argv)

def download_and_extract_font(font_url: str, font_zip: str, font_dir: str, font_file: str, font_path: str) -> None:
    os.makedirs(font_dir, exist_ok=True)
    logger.warning(f"Font not found. Downloading font from {font_url}")
    urllib.request.urlretrieve(font_url, font_zip)
    with zipfile.ZipFile(font_zip, 'r') as zip_ref:
        zip_ref.extract(font_file, font_dir)
    os.remove(font_zip)
    logger.info(f"Font downloaded and extracted to {font_path}")

def main() -> None:
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

    if not os.path.isfile(config.FONT_PATH):
        download_and_extract_font(
            font_url="https://dl.dafont.com/dl/?f=bebas_neue",
            font_zip="bebas_neue.zip",
            font_dir=os.path.dirname(config.FONT_PATH),
            font_file=os.path.basename(config.FONT_PATH),
            font_path=config.FONT_PATH
        )
        assert os.path.isfile(config.FONT_PATH), f"Font file {config.FONT_PATH} not found after download."

    if no_backend:
        makeradmin_client: MockedMakerAdminClient | MakerAdminClient = MockedMakerAdminClient(base_url=config.maker_admin_base_url,
                                                   token_path=config.makeradmin_token_filename)
    else:
        makeradmin_client = MakerAdminClient(base_url=ns.maker_admin_base_url, token_path=config.makeradmin_token_filename)

    if no_slack:
        slack_client: MockSlackClient | SlackClient = MockSlackClient(token_path=config.slack_token_filename, channel_id=ns.slack_channel_id)
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
