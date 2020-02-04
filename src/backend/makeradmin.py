import requests
from src.util.logger import get_logger
from json.decoder import JSONDecodeError
from getpass import getpass
import sys

logger = get_logger()

class MakerAdminClient(object):
    TAG_URL = "/multiaccess/memberbooth/tag"
    MEMBER_NUMBER_URL = '/multiaccess/memberbooth/member'

    def __init__(self, base_url=None, token=""):
        self.base_url = base_url
        self.token = token

    def request(self, subpage, data={}):
        url = self.base_url + subpage
        r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token}, data=data)
        return r

    def is_logged_in(self):
        if not self.token:
            return False
        r = self.request(self.TAG_URL, {"tagid": 0})
        if not r.ok:
            data = r.json()
            logger.warning(f"Token not logged in with correct permissions. Got: '{data}'")
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
        self.token = getpass("\ttoken: ")
        if not self.is_logged_in():
            logger.warning("Login failed")
            return False
        logger.info("Login successful")
        return True
