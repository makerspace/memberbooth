import requests
from src.util.logger import get_logger
from src.util.token_config import TokenConfiguredClient, TokenExpiredError
from pathlib import Path


logger = get_logger()


class NetworkError(Exception):
    pass


class MakerAdminTokenExpiredError(TokenExpiredError):
    pass


class IncorrectPinCode(KeyError):
    def __init__(self, member_number: str):
        super().__init__(f"Wrong pin code for member number: {member_number}")


class MakerAdminClient(TokenConfiguredClient):
    TAG_URL = "/multiaccess/memberbooth/tag"
    MEMBER_NUMBER_URL = '/multiaccess/memberbooth/member'
    PIN_CODE_LOGIN_URL = '/multiaccess/memberbooth/pin-login'

    def __init__(self, base_url: str, token_path: str, token=None):
        self.base_url = base_url
        self.token_path = token_path
        if Path(self.token_path).exists() and token is None:
            with open(self.token_path) as f:
                token = f.read().strip()
        if token:
            self.configure_client(token)
        else:
            logger.warning(f"Could not find a makeradmin login token at {self.token_path}. Will not connect to makeradmin.")

    def configure_client(self, token: str):
        self.token = token

    def try_log_in(self):
        if not self.is_logged_in():
            raise MakerAdminTokenExpiredError()

    def _request(self, subpage, data={}):
        assert self.token is not None
        url = self.base_url + subpage
        try:
            r = requests.get(url, headers={'Authorization': 'Bearer ' + self.token}, data=data, timeout=1)
        except requests.exceptions.RequestException:
            logger.exception("An exception was raised while trying to send request to makeradmin")
            raise NetworkError()
        return r

    @TokenConfiguredClient.require_configured_factory(default_retval=dict(ok=False))
    def request(self, subpage, data={}):
        return self._request(subpage, data)

    def is_logged_in(self) -> bool:
        if not self.token:
            return False
        r = self._request(self.TAG_URL, {"tagid": 0})
        if not r.ok:
            data = r.json()
            logger.warning(f"Token not logged in with correct permissions. Got: '{data}'")
        return r.ok

    def get_tag_info(self, tagid: int):
        r = self.request(self.TAG_URL, {"tagid": tagid})
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()

    def get_member_number_info(self, member_number: str):
        r = self.request(self.MEMBER_NUMBER_URL, {"member_number": member_number})
        if not r.ok:
            raise Exception("Could not get a response... from server")
        return r.json()

    def get_member_with_pin(self, member_number: str, pin_code: str):
        r = self.request(self.PIN_CODE_LOGIN_URL, {"member_number": member_number, "pin_code": pin_code})
        if r.status_code == 404:
            raise IncorrectPinCode(member_number)

        if not r.ok:
            raise Exception("Bad response from backend")
        return r.json()

    def login(self):
        print("Login to Makeradmin")
        return super().login()
