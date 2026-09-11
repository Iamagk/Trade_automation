import pyotp
from SmartApi import SmartConnect
from trading_system.config.config import config
from loguru import logger

class SmartApiLogin:
    def __init__(self):
        self.api_key = config.SMARTAPI_API_KEY
        self.client_id = config.SMARTAPI_CLIENT_ID
        self.password = config.SMARTAPI_PASSWORD
        self.totp_token = config.SMARTAPI_TOTP_TOKEN
        self.smart_connect = None
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None

    def login(self):
        try:
            self.smart_connect = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.totp_token).now()
            data = self.smart_connect.generateSession(self.client_id, self.password, totp)
            
            if data['status']:
                self.auth_token = data['data']['jwtToken']
                self.refresh_token = data['data']['refreshToken']
                self.feed_token = self.smart_connect.getfeedToken()
                logger.info(f"Successfully logged in to SmartAPI for client {self.client_id}")
                return data['data']
            else:
                logger.error(f"Failed to login: {data['message']}")
                raise Exception(f"Login failed: {data['message']}")
        except Exception as e:
            logger.exception(f"Exception during SmartAPI login: {e}")
            raise

    def get_session(self):
        if not self.smart_connect or not self.auth_token:
            return self.login()
        return {
            'jwtToken': self.auth_token,
            'refreshToken': self.refresh_token,
            'feedToken': self.feed_token
        }

    def refresh_session(self):
        try:
            data = self.smart_connect.renewAccessToken(self.refresh_token)
            if data['status']:
                self.auth_token = data['data']['jwtToken']
                self.refresh_token = data['data']['refreshToken']
                logger.info("Successfully refreshed SmartAPI access token")
                return self.auth_token
            else:
                logger.error(f"Failed to refresh token: {data['message']}")
                return self.login()
        except Exception as e:
            logger.exception(f"Exception during token refresh: {e}")
            return self.login()

smart_api_login = SmartApiLogin()
