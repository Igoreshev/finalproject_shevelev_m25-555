
import requests
from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import ApiRequestError


class BaseApiClient(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict:
        pass


class CoinGeckoClient(BaseApiClient):
    def __init__(self, config):
        super().__init__(config)

    def fetch_rates(self) -> dict[str, float]:
        """
        Возвращает курсы в формате:
        {
            "BTC_USD": 59337.21,
            "ETH_USD": 3720.00,
            "SOL_USD": 145.12
        }
        """
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())

        params = {
            "ids": ids,
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }

        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko request failed: {e}")

        result: dict[str, float] = {}

        for code, cg_id in self.config.CRYPTO_ID_MAP.items():
            try:
                rate = data[cg_id][self.config.BASE_CURRENCY.lower()]
                result[f"{code}_{self.config.BASE_CURRENCY}"] = float(rate)
            except KeyError:
                
                continue

        return result


class ExchangeRateApiClient(BaseApiClient):
    def __init__(self, config):
        super().__init__(config)

    def fetch_rates(self) -> dict[str, float]:
        url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API error: {e}")

        if payload.get("result") != "success":
            raise ApiRequestError("ExchangeRate-API returned non-success result")

        rates = payload.get("conversion_rates", {})

        result = {}
        for code in self.config.FIAT_CURRENCIES:
            if code in rates:
                result[f"{code}_{self.config.BASE_CURRENCY}"] = rates[code]

        return result


