from datetime import datetime
import hashlib
import secrets
from typing import Dict


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self.username = username           
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    # ===== ГЕТТЕРЫ =====

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def registration_date(self) -> datetime:
        return self._registration_date


    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value


    def get_user_info(self) -> dict:
        """
        Возвращает информацию о пользователе без пароля
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str):
        """
        Меняет пароль пользователя с хешированием
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        new_salt = secrets.token_hex(8)
        new_hash = self._hash_password(new_password, new_salt)

        self._salt = new_salt
        self._hashed_password = new_hash

    def verify_password(self, password: str) -> bool:
        """
        Проверяет пароль на совпадение
        """
        hashed = self._hash_password(password, self._salt)
        return hashed == self._hashed_password


    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """
        Односторонний псевдо-хеш пароля
        """
        value = password + salt
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance


    @property
    def currency_code(self) -> str:
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str):
        if not value or not value.strip():
            raise ValueError("Код валюты не может быть пустым")
        self._currency_code = value.upper()

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)


    def deposit(self, amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма пополнения должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")

        self._balance += amount

    def withdraw(self, amount: float):
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма снятия должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError("Недостаточно средств на балансе")

        self._balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self._currency_code,
            "balance": self._balance,
        }

class Portfolio:
    def __init__(self, user_id: int, wallets: Dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}


    @property
    def user(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)


    def add_currency(self, currency_code: str):
        currency_code = currency_code.upper()

        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {currency_code} уже существует")

        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Wallet:
        currency_code = currency_code.upper()

        if currency_code not in self._wallets:
            raise KeyError(f"Кошелёк для валюты {currency_code} не найден")

        return self._wallets[currency_code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        base_currency = base_currency.upper()

        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.1,
            "BTC": 30000.0,
        }

        if base_currency not in exchange_rates:
            raise ValueError(f"Нет курса для базовой валюты {base_currency}")

        total = 0.0

        for currency, wallet in self._wallets.items():
            if currency not in exchange_rates:
                raise ValueError(f"Нет курса для валюты {currency}")

            value_in_usd = wallet.balance * exchange_rates[currency]
            total += value_in_usd

        return total / exchange_rates[base_currency]


    def buy_currency(self, currency_code: str, amount: float, price_in_usd: float):
        """
        Покупка валюты: списываем USD, начисляем валюту
        """
        usd_wallet = self.get_wallet("USD")
        target_wallet = self.get_wallet(currency_code)

        cost = amount * price_in_usd
        usd_wallet.withdraw(cost)
        target_wallet.deposit(amount)

    def sell_currency(self, currency_code: str, amount: float, price_in_usd: float):
        """
        Продажа валюты: списываем валюту, начисляем USD
        """
        usd_wallet = self.get_wallet("USD")
        target_wallet = self.get_wallet(currency_code)

        target_wallet.withdraw(amount)
        usd_wallet.deposit(amount * price_in_usd)