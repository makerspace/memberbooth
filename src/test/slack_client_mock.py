from src.util.logger import get_logger
import config
from src.util.slack_client import SlackClient

logger = get_logger()

class MockSlackClient(SlackClient):
    def __init__(self, token_path, channel_id, token=None):
        self.token_path = token_path
        self.channel_id = channel_id
        self.token = None

    def post_message(self, msg):
        logger.debug(f"Slack: '{msg}'")
