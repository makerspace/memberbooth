from src.util.logger import get_logger
import os
from pathlib import Path

logger = get_logger()

class TokenExpiredError(ValueError):
    pass

class TokenConfiguredClient(object):
    _configured = False
    token_path = None

    def configure_client(self, token):
        '''
        Gets called with the token when it becomes available
        '''
        raise NotImplemented()

    def try_log_in(self):
        '''
        Check if logged in. Raise a TokenExpiredError if not logged in
        '''
        raise NotImplemented()

    @property
    def configured(self):
        if not self._configured and Path(self.token_path).is_file():
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

    def require_configured(f, default_retval=None):
        def require_configured_wrapper(self, *args, **kwargs):
            if not self.configured:
                return default_retval
            return f(self, *args, **kwargs)
        return require_configured_wrapper

