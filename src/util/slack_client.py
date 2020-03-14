from src.util.logger import get_logger
import os
import slack
import config
from pathlib import Path
from src.util.token_config import TokenConfiguredClient, TokenExpiredError

logger = get_logger()

class SlackTokenExpiredError(TokenExpiredError):
    pass

class SlackClient(TokenConfiguredClient):
    def __init__(self, token_path, channel_id, token=None):
        self.client = slack.WebClient(token)
        self.token_path = token_path
        self.channel_id = channel_id
        if token:
            self.configure_client(token)

    def configure_client(self, token):
        self.client.token = token

    def try_log_in(self):
        self._post_message("Slack client reconnected")

    def _post_message(self, msg):
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=msg,
                link_names=True)
        except slack.errors.SlackApiError as e:
            raise SlackTokenExpiredError(str(e))

    @TokenConfiguredClient.require_configured_factory()
    def post_message(self, msg):
        try:
            self._post_message(msg)
        except SlackTokenExpiredError:
            logger.exception("Slack token is not valid anymore")

    def post_message_info(self, msg):
        self.post_message(msg)

    def post_message_error(self, msg):
        self.post_message("*Error*: " + msg)

    def post_message_alert(self, msg):
        if config.development:
            self.post_message(msg)
        else:
            self.post_message("@channel - " + msg)

    def login(self):
        print("Login to Slack")
        return super().login()
