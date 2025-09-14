from src.util.logger import get_logger
import os
from pathlib import Path
from getpass import getpass
from abc import ABC, abstractmethod

logger = get_logger()


class TokenExpiredError(ValueError):
    pass


class TokenConfiguredClient(ABC):
    _configured = False
    token_path: str | None = None
    token: str | None = None

    @abstractmethod
    def configure_client(self, token: str):
        '''
        Gets called with the token when it becomes available
        '''
        pass

    @abstractmethod
    def try_log_in(self):
        '''
        Check if logged in. Raise a TokenExpiredError if not logged in
        '''
        pass

    def check_configured(self):
        if not self._configured and self.token is not None:
            try:
                self.try_log_in()
                self._configured = True
                logger.info("Client logged in")
            except TokenExpiredError:
                logger.error("Token invalid")
                self._configured = False
                self.token = None
        elif not self._configured and self.token_path and Path(self.token_path).is_file():
            with open(self.token_path) as f:
                token = f.read().strip()
            self.configure_client(token)
            try:
                self.try_log_in()
                self._configured = True
                logger.info("Client logged in")
            except TokenExpiredError:
                logger.error("Token file expired. Removing it.")
                try:
                    os.remove(self.token_path)
                except FileNotFoundError:
                    pass
                self._configured = False

        return self._configured

    @property
    def configured(self):
        return self.check_configured()

    @staticmethod
    def require_configured_factory(default_retval: dict[str,bool] | None=None):
        def require_configured(f):
            def require_configured_wrapper(self, *args, **kwargs):
                if not self.configured:
                    return default_retval
                return f(self, *args, **kwargs)

            return require_configured_wrapper

        return require_configured

    def login(self):
        token = getpass("\ttoken: ")
        self.configure_client(token)
        if not self.configured:
            logger.warning("Login failed")
            return False
        logger.info("Login successful")
        return True
