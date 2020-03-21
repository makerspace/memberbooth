import requests
from src.util.logger import get_logger
from json.decoder import JSONDecodeError
from src.util.token_config import TokenConfiguredClient, TokenExpiredError
import sys

logger = get_logger()

class MakerAdminTokenExpiredError(TokenExpiredError):
    pass

class MakerAdminClient(TokenConfiguredClient):
    TAG_URL = "/multiaccess/memberbooth/tag"
    MEMBER_NUMBER_URL = '/multiaccess/memberbooth/member'

    def __init__(self, base_url, token_path, token=None):
        self.base_url = base_url
        self.token_path = token_path
        if token:
            self.configure_client(token)

    def configure_client(self, token):
        self.token = token

    def try_log_in(self):
        if not self.is_logged_in():
            raise MakerAdminTokenExpiredError()

    def _request(self, subpage, data={}):
        url = self.base_url + subpage
        r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token}, data=data)
        return r

    @TokenConfiguredClient.require_configured_factory(default_retval=dict(ok=False))
    def request(self, subpage, data={}):
        return self._request(subpage, data)

    def is_logged_in(self):
        if not self.token:
            return False
        r = self._request(self.TAG_URL, {"tagid": 0})
        if not r.ok:
            data = r.json()
            logger.info(f"Token not logged in with correct permissions. Got: '{data}'")
        return r.ok

    def get_tag_info(self, tagid:int):
        r = self.request(self.TAG_URL, {"tagid": tagid})
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()

    def get_member_number_info(self, member_number:int):
        r = self.request(self.MEMBER_NUMBER_URL, {"member_number": member_number})
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()

    def login(self):
        print("Login to Makeradmin")
        return super().login()
