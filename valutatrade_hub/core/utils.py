import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

from .models import User
from .exceptions import InsufficientFundsError, ApiRequestError
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action
from valutatrade_hub.core.currencies import get_currency




settings = SettingsLoader()

DATA_DIR: Path = settings.get("DATA_DIR")
USERS_FILE: Path = settings.get("USERS_FILE")
PORTFOLIOS_FILE: Path = settings.get("PORTFOLIOS_FILE")
RATES_FILE: Path = settings.get("RATES_FILE")
SESSION_FILE: Path = DATA_DIR / "session.json"

BASE_CURRENCY: str = settings.get("BASE_CURRENCY")
RATES_TTL_SECONDS: int = settings.get("RATES_TTL_SECONDS")



def _load_json(path: Path, default):
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except json.JSONDecodeError:
        return default


def _save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)



@log_action("REGISTER")
def register_user(username: str, password: str) -> str:
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    users = _load_json(USERS_FILE, [])

    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1

    salt = secrets.token_hex(8)
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()

    user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        salt=salt,
        registration_date=datetime.now(),
    )

    users.append(
        {
            "user_id": user.user_id,
            "username": username,
            "hashed_password": hashed_password,
            "salt": salt,
            "registration_date": user.registration_date.isoformat(),
        }
    )

    _save_json(USERS_FILE, users)

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolios.append({"user_id": user_id, "wallets": {}})
    _save_json(PORTFOLIOS_FILE, portfolios)

    return (
        f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        f"Войдите: login --username {username} --password ****"
    )


@log_action("LOGIN")
def login_user(username: str, password: str) -> str:
    users = _load_json(USERS_FILE, [])
    user_data = next((u for u in users if u["username"] == username), None)

    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    salt = user_data["salt"]
    hashed_input = hashlib.sha256((password + salt).encode()).hexdigest()

    if hashed_input != user_data["hashed_password"]:
        raise ValueError("Неверный пароль")

    session = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
    }

    _save_json(SESSION_FILE, session)
    return f"Вы вошли как '{username}'"



def show_portfolio(base_currency: str | None = None) -> str:
    base_currency = normalize_currency_code(base_currency or BASE_CURRENCY)

    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next(p for p in portfolios if p["user_id"] == session["user_id"])

    if not portfolio.get("wallets"):
        return f"Портфель пользователя '{session['username']}' пуст"

    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59300.0,
        "ETH": 3700.0,
        "RUB": 0.010,
    }

    if base_currency not in exchange_rates:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

    total = 0.0
    lines = []

    for code, wallet in portfolio["wallets"].items():
        if code not in exchange_rates:
            continue

        balance = wallet["balance"]
        usd_value = balance * exchange_rates[code]
        base_value = usd_value / exchange_rates[base_currency]

        total += base_value
        lines.append(
            f"- {code}: {balance:.4f} → {base_value:,.2f} {base_currency}"
        )

    return "\n".join(
        [
            f"Портфель пользователя '{session['username']}' (база: {base_currency}):",
            *lines,
            "-" * 33,
            f"ИТОГО: {total:,.2f} {base_currency}",
        ]
    )



@log_action("BUY")
def buy_currency(currency_code: str, amount: float) -> str:
    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    currency_code = normalize_currency_code(currency_code)
    amount = validate_amount(amount)
    currency = get_currency(currency_code)

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next(
        p for p in portfolios if p["user_id"] == session["user_id"]
    )

    wallets = portfolio.setdefault("wallets", {})
    wallet = wallets.setdefault(currency.code, {"balance": 0.0})

    old_balance = wallet["balance"]
    wallet["balance"] = round(old_balance + amount, 8)

    _save_json(PORTFOLIOS_FILE, portfolios)

    rate = get_rate(currency.code, BASE_CURRENCY, silent=True)
    cost = amount * rate

    return (
        f"Покупка выполнена: {amount:.4f} {currency.code}\n"
        f"- {currency.code}: было {old_balance:.4f} → стало {wallet['balance']:.4f}\n"
        f"Оценочная стоимость покупки: {cost:,.2f} {BASE_CURRENCY}"
    )


@log_action("SELL")
def sell_currency(currency_code: str, amount: float) -> str:
    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    currency_code = normalize_currency_code(currency_code)
    amount = validate_amount(amount)
    currency = get_currency(currency_code)

    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next(
        p for p in portfolios if p["user_id"] == session["user_id"]
    )

    wallets = portfolio.get("wallets", {})

    if currency.code not in wallets:
        raise ValueError(
            f"У вас нет кошелька '{currency.code}'. "
            "Он создаётся автоматически при первой покупке."
        )

    wallet = wallets[currency.code]
    old_balance = wallet["balance"]

    if old_balance < amount:
        raise InsufficientFundsError(
            available=old_balance,
            required=amount,
            code=currency.code,
        )

    wallet["balance"] = round(old_balance - amount, 8)
    _save_json(PORTFOLIOS_FILE, portfolios)

    rate = get_rate(currency.code, BASE_CURRENCY, silent=True)
    revenue = amount * rate

    return (
        f"Продажа выполнена: {amount:.4f} {currency.code}\n"
        f"- {currency.code}: было {old_balance:.4f} → стало {wallet['balance']:.4f}\n"
        f"Оценочная выручка: {revenue:,.2f} {BASE_CURRENCY}"
    )


def get_rate(from_code: str, to_code: str, silent: bool = False) -> float | str:
    from_code = normalize_currency_code(from_code)
    to_code = normalize_currency_code(to_code)

    from_currency = get_currency(from_code)
    to_currency = get_currency(to_code)

    now = datetime.now()
    rates = _load_json(RATES_FILE, {})

    pair_key = f"{from_currency.code}_{to_currency.code}"

    if pair_key in rates:
        updated_at = datetime.fromisoformat(rates[pair_key]["updated_at"])
        if (now - updated_at).total_seconds() < RATES_TTL_SECONDS:
            rate = rates[pair_key]["rate"]
            return rate if silent else (
                f"Курс {from_currency.code}→{to_currency.code}: {rate:.8f}\n"
                f"(обновлено: {updated_at.isoformat()})"
            )

    fake_rates = {
        "USD_BTC": 1 / 59337.21,
        "BTC_USD": 59337.21,
        "EUR_USD": 1.0786,
        "USD_EUR": 1 / 1.0786,
        "ETH_USD": 3720.00,
        "USD_ETH": 1 / 3720.00,
    }

    if pair_key not in fake_rates:
        raise ApiRequestError(
            f"Нет данных для {from_currency.code}→{to_currency.code}"
        )

    rate = fake_rates[pair_key]

    rates[pair_key] = {
        "rate": rate,
        "updated_at": now.isoformat(),
    }
    rates["last_refresh"] = now.isoformat()
    rates["source"] = "Stub"

    _save_json(RATES_FILE, rates)

    return rate if silent else (
        f"Курс {from_currency.code}→{to_currency.code}: {rate:.8f}\n"
        f"(обновлено: {now.isoformat()})"
    )


def normalize_currency_code(code: str) -> str:
    """
    Приводит код валюты к верхнему регистру и валидирует формат
    """
    if not isinstance(code, str):
        raise ValueError("Код валюты должен быть строкой")

    code = code.strip().upper()

    if not (2 <= len(code) <= 5) or " " in code:
        raise ValueError(f"Некорректный код валюты '{code}'")

    return code


def validate_amount(amount) -> float:
    """
    Проверяет, что amount — положительное число
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть числом")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    return amount
