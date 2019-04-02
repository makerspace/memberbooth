import requests
from logging import basicConfig, INFO, getLogger
import sys

logger = getLogger("memberbooth")
basicConfig(format='%(asctime)s %(levelname)s [%(process)d/%(threadName)s %(pathname)s:%(lineno)d]: %(message)s', stream=sys.stderr, level=INFO)

class MakerAdminClient(object):

    def __init__(self, base_url=None, token=""):
        self.base_url = base_url
        self.token = token

    def request(self, subpage):
        url = self.base_url + subpage
        r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token})
        return r

    def is_logged_in(self):
        r = self.request("/membership/permission/")
        return r.ok

    def get_tag_info(self, tagid:int):
        r = self.request("/multiaccess/keylookup/" + str(tagid))
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
