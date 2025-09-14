from src.util.logger import get_logger
from src.util.slack_client import SlackClient

logger = get_logger()


class MockSlackClient(SlackClient):
    def __init__(self, token_path: str, channel_id: str | None, token: str | None = None) -> None:
        self.token_path = token_path
        self.channel_id = channel_id or "<no-channel>"
        self.token = None

    def post_message(self, msg: str) -> None:
        logger.debug(f"Slack: '{msg}'")
