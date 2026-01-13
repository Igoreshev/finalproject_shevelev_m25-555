# finalproject_shevelev_m25-555

### ValutaTrade Hub

### Консольный сервис управления валютным портфелем
ValutaTrade Hub — это консольное Python-приложение для управления пользовательскими валютными портфелями с поддержкой фиатных и криптовалют.
Проект реализован с разделением на несколько логических сервисов:
Core Service — бизнес-логика приложения
Parser Service — отдельный сервис для получения и обновления курсов валют
CLI — командный интерфейс пользователя
Основная идея проекта — разделить работу с данными, бизнес-логику и внешние API, чтобы система была:
расширяемой;
устойчивой к ошибкам;
понятной для сопровождения.

### Возможности приложения
Пользователь через CLI может:
зарегистрироваться в системе;
войти в систему (логин);
просмотреть свой портфель;
купить валюту;
продать валюту;
получить текущий курс валют;
вручную обновить курсы валют;
работать с локальным кешем курсов без постоянных API-запросов.

### Архитектура проекта
Core Service отвечает за всю бизнес-логику приложения и никогда напрямую не обращается к внешним API.
Основные задачи Core Service:
управление пользователями;
управление портфелями и кошельками;
валидация входных данных;
расчёт стоимости портфеля;
чтение актуальных курсов из локального кеша (rates.json);
генерация пользовательских ошибок.
Core Service работает только с локальными JSON-файлами и не зависит от источников курсов.
Parser Service
Parser Service — отдельный сервис, отвечающий за сбор курсов валют.
Он:
обращается к внешним API;
обрабатывает ответы;
валидирует данные;
сохраняет историю курсов;
обновляет актуальный снимок курсов.
Источники данных:
CoinGecko — криптовалюты (BTC, ETH, SOL и др.);
ExchangeRate-API — фиатные валюты (EUR, GBP, RUB и др.).
Parser Service может запускаться:
вручную через CLI;
автоматически (в будущем — по расписанию).
CLI (Command Line Interface)
CLI — это единственная точка входа для пользователя.
CLI:
принимает команды;
парсит аргументы;
вызывает соответствующие usecases;
перехватывает исключения;
выводит понятные сообщения пользователю.
CLI не содержит бизнес-логики.

### Структура проекта

|-- Makefile
|-- README.md
|-- data
|   |-- exchange_rates.json
|   |-- portfolios.json
|   |-- rates.json
|   |-- session.json
|   `-- users.json
|-- dist
|   |-- finalproject_shevelev_m25_555-0.1.0-py3-none-any.whl
|   `-- finalproject_shevelev_m25_555-0.1.0.tar.gz
|-- logs
|   `-- actions.log
|-- poetry.lock
|-- pyproject.toml
`-- valutatrade_hub
    |   |-- decorators.cpython-312.pyc
    |   |-- logging_config.cpython-312.pyc
    |   `-- main.cpython-312.pyc
    |-- cli
    |   `-- interface.py
    |-- core
    |   |-- currencies.py
    |   |-- exceptions.py
    |   |-- models.py
    |   |-- usecases.py
    |   `-- utils.py
    |-- decorators.py
    |-- infra
    |   `-- settings.py
    |-- logging_config.py
    |-- main.py
    `-- parser_service
        |-- api_clients.py
        |-- config.py
        |-- storage.py
        `-- updater.py

13 directories, 33 files
(finalproject-shevelev-m25-555-py3.12)

### Иерархия валют
В проекте реализована иерархия валют:
Currency — абстрактный базовый класс
FiatCurrency — фиатные валюты
CryptoCurrency — криптовалюты
Каждая валюта:
имеет код (USD, BTC, ETH);
валидируется при создании;
имеет единый интерфейс отображения.
Получение валюты осуществляется через фабрику get_currency(code).

### Пользовательские исключения
Используются собственные исключения:
недостаточно средств;
неизвестная валюта;
устаревшие курсы;
ошибки внешних API.
Исключения:
генерируются в Core Service;
корректно перехватываются в CLI;
выводятся пользователю в понятном виде.

### Singleton-конфигурация
Для хранения настроек используется паттерн Singleton.
Через SettingsLoader загружаются:
пути к JSON-файлам;
TTL курсов;
базовая валюта;
параметры логирования.
Гарантируется, что в приложении существует только один экземпляр конфигурации.

### Логирование
Реализован декоратор @log_action.
Логируются операции:
регистрация;
вход;
покупка валюты;
продажа валюты.
Логи записываются в файл:
logs/actions.log
Формат:
INFO 2026-01-06 BUY user='alice' currency='BTC' amount=0.05 result=OK

### Parser Service: хранение курсов
exchange_rates.json
История всех измерений курсов:
каждая запись уникальна;
хранит источник, время и метаданные;
не перезаписывается.
rates.json
Актуальный снимок курсов:
хранится по валютным парам;
содержит время обновления;
используется Core Service;
имеет TTL актуальности.

### Команды CLI
Регистрация
poetry run project register --username alice --password 1234
Вход в систему
poetry run project login --username alice --password 1234
Просмотр портфеля
poetry run project show-portfolio
Просмотр с указанием базовой валюты
poetry run project show-portfolio --base USD
Покупка валюты
poetry run project buy --currency BTC --amount 0.05
Продажа валюты
poetry run project sell --currency BTC --amount 0.01
Получение курса
poetry run project get-rate --from BTC --to USD
Обновление курсов
poetry run project update-rates
Просмотр курсов из локального кеша 
poetry run project show-rates
Фильтрация по валюте
poetry run project show-rates --currency BTC
Топ курсов 
poetry run project show-rates --top 5
