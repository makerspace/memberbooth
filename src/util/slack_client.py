from src.util.logger import get_logger
import os
import slack
import config
from pathlib import Path

logger = get_logger()

class SlackTokenExpiredError(ValueError):
    pass

class SlackClient():
    def __init__(self, token_path, channel_id, token=None):
        self.configured = False
        self.client = slack.WebClient(token)
        self.token_path = token_path
        self.channel_id = channel_id
        if token:
            self.configure(token)

    def configure(self, token):
        self.client.token = token
        self.configured = True

    def check_configured(self):
        if not self.configured and Path(self.token_path).is_file():
            with open(self.token_path) as f:
                token = f.read()
            self.configure(token)
            try:
                self._post_message("Slack client reconnected")
                logger.info("Slack client reconnected")
            except SlackTokenExpiredError:
                logger.error("Slack token file expired. Removing it.")
                try:
                    os.remove(self.token_path)
                except FileNotFoundError:
                    pass

    def _post_message(self, msg):
        if not self.configured:
            return

        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=msg,
                link_names=True)
        except slack.errors.SlackApiError as e:
            self.configured = False
            logger.error(f"SlackClient failed with error: {e}")
            raise SlackTokenExpiredError(str(e))

    def post_message(self, msg):
        self.check_configured()

        try:
            self._post_message(msg)
        except SlackTokenExpiredError:
            logger.error("Slack token is not valid anymore")


    def post_message_info(self, msg):
        self.post_message(msg)

    def post_message_error(self, msg):
        self.post_message("*Error*: " + msg)

    def post_message_alert(self, msg):
        if config.development:
            self.post_message(msg)
        else:
            self.post_message("@channel - " + msg)
