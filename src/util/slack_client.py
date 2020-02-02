from src.util.logger import get_logger
import os
import slack

logger = get_logger()

SLACK_CLIENT = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])

class SlackClient():

    def __init__(self):
        self.client = SLACK_CLIENT

    def post_message(self, msg):
        try:
            response = self.client.chat_postMessage(
                channel="GPWJU7NF9",
                text=msg,
                link_names=True)
        except slack.errors.SlackApiError as e:
            logger.error(f"SlackClient failed with error: {e}")
        except:
            logger.error(f"SlackClient failed with unspecified error.")

    def post_message_info(self, msg):
        self.post_message(msg)

    def post_message_error(self, msg):
        self.post_message("*Error*: " + msg)

    def post_message_alert(self, msg):
        self.post_message("@channel - " + msg)
