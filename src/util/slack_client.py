from src.util.logger import get_logger
import os
import slack
import config
from pathlib import Path

logger = get_logger()

slack_configured = False
slack_client = None

class SlackClient():

    def __init__(self):
        self.client = slack_client

    def post_message(self, msg):
        global slack_client
        global slack_configured

        if not config.slack_token_path or not config.slack_log_channel_id:
            return

        if not slack_configured and Path(config.slack_token_path).is_file():

            f = open(config.slack_token_path, 'r')
            slack_token = f.read()
            f.close()

            slack_client = slack.WebClient(slack_token)
            self.client = slack_client
            slack_configured = True

        try:
            response = self.client.chat_postMessage(
                channel=config.slack_log_channel_id,
                text=msg,
                link_names=True)
        except slack.errors.SlackApiError as e:
            slack_configured = False
            logger.error(f"SlackClient failed with error: {e}")
        except:
            slack_configured = False
            logger.error(f"SlackClient failed with unspecified error.")

    def post_message_info(self, msg):
        self.post_message(msg)

    def post_message_error(self, msg):
        self.post_message("*Error*: " + msg)

    def post_message_alert(self, msg):
        if config.development:
            self.post_message(msg)
        else:
            self.post_message("@channel - " + msg)
