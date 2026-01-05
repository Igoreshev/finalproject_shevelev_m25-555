
from abc import ABC, abstractmethod
from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Currency name must be a non-empty string")

        if (
            not isinstance(code, str)
            or not code.isupper()
            or not (2 <= len(code) <= 5)
            or " " in code
        ):
            raise ValueError(
                "Currency code must be uppercase, 2–5 characters, without spaces"
            )

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Return human-readable representation for UI/logs"""
        pass


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)

        if not isinstance(issuing_country, str) or not issuing_country.strip():
            raise ValueError("Issuing country must be a non-empty string")

        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    def __init__(
        self,
        name: str,
        code: str,
        algorithm: str,
        market_cap: float,
    ):
        super().__init__(name, code)

        if not isinstance(algorithm, str) or not algorithm.strip():
            raise ValueError("Algorithm must be a non-empty string")

        if not isinstance(market_cap, (int, float)) or market_cap <= 0:
            raise ValueError("Market cap must be a positive number")

        self.algorithm = algorithm
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


_CURRENCY_REGISTRY = {
    "USD": FiatCurrency(
        name="US Dollar",
        code="USD",
        issuing_country="United States",
    ),
    "EUR": FiatCurrency(
        name="Euro",
        code="EUR",
        issuing_country="Eurozone",
    ),
    "BTC": CryptoCurrency(
        name="Bitcoin",
        code="BTC",
        algorithm="SHA-256",
        market_cap=1.12e12,
    ),
    "ETH": CryptoCurrency(
        name="Ethereum",
        code="ETH",
        algorithm="Ethash",
        market_cap=4.5e11,
    ),
}


def get_currency(code: str) -> Currency:
    if not isinstance(code, str):
        raise ValueError("Currency code must be a string")

    code = code.upper()

    try:
        return _CURRENCY_REGISTRY[code]
    except KeyError:
        raise CurrencyNotFoundError(code)
