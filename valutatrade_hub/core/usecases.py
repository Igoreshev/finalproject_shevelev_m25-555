import json
from pathlib import Path
from datetime import datetime
import hashlib
import secrets
from datetime import timedelta
from .models import User

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
SESSION_FILE = DATA_DIR / "session.json"

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


def register_user(username: str, password: str) -> str:
    # ===== ВАЛИДАЦИЯ =====
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    # ===== ЗАГРУЗКА ДАННЫХ =====
    users = _load_json(USERS_FILE, [])

    # ===== ПРОВЕРКА УНИКАЛЬНОСТИ =====
    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    # ===== ГЕНЕРАЦИЯ ID =====
    user_id = max((u["user_id"] for u in users), default=0) + 1

    # ===== ХЕШИРОВАНИЕ ПАРОЛЯ =====
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

    # ===== СОЗДАНИЕ ПУСТОГО ПОРТФЕЛЯ =====
    portfolios = _load_json(PORTFOLIOS_FILE, [])

    portfolios.append(
        {
            "user_id": user_id,
            "wallets": {},
        }
    )

    _save_json(PORTFOLIOS_FILE, portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"

def login_user(username: str, password: str) -> str:
    users = _load_json(USERS_FILE, [])

    # ===== ПОИСК ПОЛЬЗОВАТЕЛЯ =====
    user_data = next((u for u in users if u["username"] == username), None)

    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    # ===== ПРОВЕРКА ПАРОЛЯ =====
    salt = user_data["salt"]
    hashed_input = hashlib.sha256((password + salt).encode()).hexdigest()

    if hashed_input != user_data["hashed_password"]:
        raise ValueError("Неверный пароль")

    # ===== СОХРАНЕНИЕ СЕССИИ =====
    session = {
        "user_id": user_data["user_id"],
        "username": user_data["username"],
    }

    _save_json(SESSION_FILE, session)

    return f"Вы вошли как '{username}'"


def show_portfolio(base_currency: str = "USD") -> str:
    base_currency = base_currency.upper()

    # ===== ПРОВЕРКА СЕССИИ =====
    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    user_id = session["user_id"]
    username = session["username"]

    # ===== ЗАГРУЗКА ПОРТФЕЛЯ =====
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next((p for p in portfolios if p["user_id"] == user_id), None)

    if not portfolio or not portfolio.get("wallets"):
        return f"Портфель пользователя '{username}' пуст"

    # ===== ЗАГЛУШКА КУРСОВ =====
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59300.0,
        "RUB": 0.010,
        "ETH": 3700.0,
    }

    if base_currency not in exchange_rates:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

    lines = []
    total_in_base = 0.0

    for currency, data in portfolio["wallets"].items():
        if currency not in exchange_rates:
            continue

        balance = data["balance"]
        value_in_usd = balance * exchange_rates[currency]
        value_in_base = value_in_usd / exchange_rates[base_currency]

        total_in_base += value_in_base

        lines.append(
            f"- {currency}: {balance:.4f}  → {value_in_base:,.2f} {base_currency}"
        )

    header = f"Портфель пользователя '{username}' (база: {base_currency}):"
    footer = f"ИТОГО: {total_in_base:,.2f} {base_currency}"

    result = "\n".join(
        [header] + lines + ["-" * 33, footer]
    )

    return result

def buy_currency(currency: str, amount: float) -> str:
    # ===== ПРОВЕРКА СЕССИИ =====
    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    # ===== ВАЛИДАЦИЯ =====
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Некорректный код валюты")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    base_currency = "USD"

    # ===== ЗАГРУЗКА КУРСОВ (ЗАГЛУШКА) =====
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59300.0,
        "ETH": 3700.0,
    }

    if currency not in exchange_rates:
        raise ValueError(f"Не удалось получить курс для {currency}→{base_currency}")

    rate = exchange_rates[currency]

    # ===== ЗАГРУЗКА ПОРТФЕЛЕЙ =====
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next(
        (p for p in portfolios if p["user_id"] == session["user_id"]),
        None,
    )

    if not portfolio:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio.setdefault("wallets", {})

    # ===== АВТОСОЗДАНИЕ КОШЕЛЬКА =====
    wallet = wallets.setdefault(currency, {"balance": 0.0})
    old_balance = wallet["balance"]

    wallet["balance"] = round(old_balance + amount, 8)

    _save_json(PORTFOLIOS_FILE, portfolios)

    total_cost = amount * rate

    return (
        f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet['balance']:.4f}\n"
        f"Оценочная стоимость покупки: {total_cost:,.2f} USD"
    )

def sell_currency(currency: str, amount: float) -> str:
    # ===== ПРОВЕРКА СЕССИИ =====
    session = _load_json(SESSION_FILE, {})
    if not session:
        raise ValueError("Сначала выполните login")

    # ===== ВАЛИДАЦИЯ =====
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Некорректный код валюты")

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть положительным числом")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    base_currency = "USD"

    # ===== КУРСЫ (ЗАГЛУШКА) =====
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59800.0,
        "ETH": 3700.0,
    }

    if currency not in exchange_rates:
        raise ValueError(f"Не удалось получить курс для {currency}→{base_currency}")

    rate = exchange_rates[currency]

    # ===== ЗАГРУЗКА ПОРТФЕЛЯ =====
    portfolios = _load_json(PORTFOLIOS_FILE, [])
    portfolio = next(
        (p for p in portfolios if p["user_id"] == session["user_id"]),
        None,
    )

    if not portfolio:
        raise ValueError("Портфель пользователя не найден")

    wallets = portfolio.get("wallets", {})

    if currency not in wallets:
        raise ValueError(
            f"У вас нет кошелька '{currency}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    wallet = wallets[currency]
    old_balance = wallet["balance"]

    if old_balance < amount:
        raise ValueError(
            f"Недостаточно средств: доступно {old_balance:.4f} {currency}, "
            f"требуется {amount:.4f} {currency}"
        )

    wallet["balance"] = round(old_balance - amount, 8)

    _save_json(PORTFOLIOS_FILE, portfolios)

    revenue = amount * rate

    return (
        f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
        f"Изменения в портфеле:\n"
        f"- {currency}: было {old_balance:.4f} → стало {wallet['balance']:.4f}\n"
        f"Оценочная выручка: {revenue:,.2f} USD"
    )

def get_rate(from_currency: str, to_currency: str) -> str:
    # ===== ВАЛИДАЦИЯ =====
    if not from_currency or not to_currency:
        raise ValueError("Коды валют не могут быть пустыми")

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    pair_key = f"{from_currency}_{to_currency}"
    reverse_key = f"{to_currency}_{from_currency}"

    now = datetime.now()

    # ===== ЗАГРУЗКА КЕША =====
    rates = _load_json(DATA_DIR / "rates.json", {})

    def is_fresh(rate_data: dict) -> bool:
        updated_at = datetime.fromisoformat(rate_data["updated_at"])
        return now - updated_at < timedelta(minutes=5)

    # ===== ЕСЛИ КУРС ЕСТЬ И ОН СВЕЖИЙ =====
    if pair_key in rates and "rate" in rates[pair_key]:
        if is_fresh(rates[pair_key]):
            rate = rates[pair_key]["rate"]
            updated_at = rates[pair_key]["updated_at"]
            reverse_rate = 1 / rate

            return (
                f"Курс {from_currency}→{to_currency}: {rate:.8f} "
                f"(обновлено: {updated_at})\n"
                f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.2f}"
            )

    # ===== ЗАГЛУШКА КУРСОВ (Parser Service позже) =====
    fake_rates = {
        "USD_BTC": 1 / 59337.21,
        "BTC_USD": 59337.21,
        "EUR_USD": 1.0786,
        "USD_EUR": 1 / 1.0786,
        "ETH_USD": 3720.00,
        "USD_ETH": 1 / 3720.00,
    }

    if pair_key not in fake_rates:
        raise ValueError(
            f"Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже."
        )

    rate = fake_rates[pair_key]

    rates[pair_key] = {
        "rate": rate,
        "updated_at": now.isoformat(),
    }
    rates["source"] = "Stub"
    rates["last_refresh"] = now.isoformat()

    _save_json(DATA_DIR / "rates.json", rates)

    reverse_rate = 1 / rate

    return (
        f"Курс {from_currency}→{to_currency}: {rate:.8f} "
        f"(обновлено: {now.strftime('%Y-%m-%d %H:%M:%S')})\n"
        f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.2f}"
    )