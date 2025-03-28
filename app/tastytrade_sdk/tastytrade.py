# app/tastytrade_sdk/tastytrade.py
from injector import Injector

from app.tastytrade_sdk.config import Config
from app.tastytrade_sdk.api import Api, RequestsSession
from app.tastytrade_sdk.market_data.market_data import MarketData


class Tastytrade:
    """
    The SDK's top-level class
    """

    def __init__(self, api_base_url: str = 'api.tastytrade.com'):
        """
        :param api_base_url: Optionally override the base URL used by the API
        (when using the sandbox environment, for e.g.)
        """

        def __configure(binder):
            binder.bind(Config, to=Config(api_base_url=api_base_url))

        self.__container = Injector(__configure)

    def login(self, login: str, password: str) -> 'Tastytrade':
        """
        Initialize a logged-in session
        """
        self.__container.get(RequestsSession).login(login, password)
        return self

    def logout(self) -> None:
        """
        End the session
        """
        self.api.delete('/sessions')

    @property
    def market_data(self) -> MarketData:
        """
        Access the MarketData submodule
        """
        return self.__container.get(MarketData)

    @property
    def api(self) -> Api:
        """
        Access the Api submodule
        """
        return self.__container.get(Api)
