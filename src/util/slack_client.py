from src.util.logger import get_logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError, SlackClientError
import config
import socket
from src.util.token_config import TokenConfiguredClient, TokenExpiredError
import urllib.error


logger = get_logger()

hostname = socket.gethostname()


class SlackTokenExpiredError(TokenExpiredError):
    pass


class SlackClient(TokenConfiguredClient):
    def __init__(self, token_path: str, channel_id: str, timeout: int = 1, token: str | None = None):
        self.client = WebClient(token, timeout=timeout)
        self.token_path = token_path
        self.channel_id = channel_id
        if token:
            self.configure_client(token)

    def configure_client(self, token: str) -> None:
        self.token = self.client.token = token

    def try_log_in(self) -> None:
        self._post_message("Slack client reconnected")

    def _post_message(self, msg: str) -> None:
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=f"{hostname}: {msg}",
                link_names=True)
            if not response['ok']:
                logger.error(f'Slack error, response = {response}')
        except SlackApiError as e:
            raise SlackTokenExpiredError(str(e))
        except SlackClientError as e:
            logger.exception(f'Slack error, error = {e}')
        except urllib.error.URLError as e:
            logger.error(f"Could not connect to Slack backend: {e}")

    @TokenConfiguredClient.require_configured_factory()
    def post_message(self, msg: str) -> None:
        try:
            self._post_message(msg)
        except SlackTokenExpiredError:
            logger.exception("Slack token is not valid anymore")

    def post_message_info(self, msg: str) -> None:
        self.post_message(msg)

    def post_message_error(self, msg: str) -> None:
        self.post_message("*Error*: " + msg)

    def post_message_alert(self, msg: str) -> None:
        if config.development:
            self.post_message(msg)
        else:
            self.post_message("@channel - " + msg)

    def login(self) -> bool:
        print("Login to Slack")
        return super().login()
