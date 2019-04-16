import requests
from logging import basicConfig, INFO, getLogger
import sys

logger = getLogger("memberbooth")

class MakerAdminClient(object):
    TAG_URL = "/multiaccess/memberbooth/tag/"
    

    def __init__(self, base_url=None, token=""):
        self.base_url = base_url
        self.token = token

    def request(self, subpage):
        url = self.base_url + subpage
        r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token})
        return r

    def is_logged_in(self):
        r = self.request(self.TAG_URL + "0")
        return r.ok

    def get_tag_info(self, tagid:int):
        r = self.request(self.TAG_URL + str(tagid))
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()

    def get_member_number_info(self, member_number:int):
        
        MEMBER_NUMBER_URL = '/multiaccess/box-terminator/member'

        url = self.base_url + MEMBER_NUMBER_URL
        
        r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token}, data={'member_number': str(member_number)})
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()
    
    def login(self):
        username, password = self.ui.promt__login()
        r = requests.post(self.base_url + "/oauth/token",
                          {"grant_type": "password", "username": username, "password": password})
        if not r.ok:
            logger.error("login failed", r)
            return False
        logger.info("login successful")
        self.token = r.json()["access_token"]
        return True
