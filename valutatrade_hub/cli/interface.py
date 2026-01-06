import argparse
from valutatrade_hub.core.usecases import (
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    get_rate,
)

from valutatrade_hub.core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.core.usecases import show_rates


def run_cli():
    parser = argparse.ArgumentParser(prog="valutatrade-hub")
    subparsers = parser.add_subparsers(dest="command")

    # register
    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--username", required=True)
    register_parser.add_argument("--password", required=True)

    # login
    login_parser = subparsers.add_parser("login")
    login_parser.add_argument("--username", required=True)
    login_parser.add_argument("--password", required=True)

    # show-portfolio
    show_parser = subparsers.add_parser("show-portfolio")
    show_parser.add_argument("--base", default="USD")

    # buy
    buy_parser = subparsers.add_parser("buy")
    buy_parser.add_argument("--currency", required=True)
    buy_parser.add_argument("--amount", required=True, type=float)

    # sell
    sell_parser = subparsers.add_parser("sell")
    sell_parser.add_argument("--currency", required=True)
    sell_parser.add_argument("--amount", required=True, type=float)

    # get-rate
    rate_parser = subparsers.add_parser("get-rate", help="Получить курс валют")
    rate_parser.add_argument("--from", dest="from_currency", required=True)
    rate_parser.add_argument("--to", dest="to_currency", required=True)

    # update-rates
    update_parser = subparsers.add_parser(
        "update-rates",
    help="Обновить курсы валют (Parser Service)",
    )
    update_parser.add_argument(
    "--source",
    choices=["coingecko", "exchangerate"],
    help="Источник курсов (по умолчанию — все)",
    )

    # show-rates
    show_rates_parser = subparsers.add_parser(
        "show-rates",
        help="Показать курсы из локального кеша",
    )
    show_rates_parser.add_argument("--currency")
    show_rates_parser.add_argument("--top", type=int)
    show_rates_parser.add_argument("--base")


    args = parser.parse_args()

    try:
        if args.command == "register":
            print(register_user(args.username, args.password))

        elif args.command == "login":
            print(login_user(args.username, args.password))

        elif args.command == "show-portfolio":
            print(show_portfolio(args.base))

        elif args.command == "buy":
            print(buy_currency(args.currency, args.amount))

        elif args.command == "sell":
            print(sell_currency(args.currency, args.amount))

        elif args.command == "get-rate":
            print(get_rate(args.from_currency, args.to_currency))


        elif args.command == "update-rates":
            print("INFO: Starting rates update...")

            try:
                config = ParserConfig()

                clients = []

                if args.source in (None, "coingecko"):
                    clients.append(CoinGeckoClient(config))

                if args.source in (None, "exchangerate"):
                    clients.append(ExchangeRateApiClient(config))

                storage = RatesStorage(config)
                updater = RatesUpdater(clients, storage)

                total = updater.run_update()

                print(
                    f"Update successful. Total rates updated: {total}. "
                    f"Last refresh: {storage.get_last_refresh()}"
                )

            except ApiRequestError as e:
                print(f"ERROR: {e}")
                print("Update completed with errors. Check logs/parser.log for details.")

        elif args.command == "show-rates":
            print(
                show_rates(
                    currency=args.currency,
                    top=args.top,
                    base=args.base,
                )
            )


        else:
            parser.print_help()

    except InsufficientFundsError as e:
        print(e)

    except CurrencyNotFoundError as e:
        print(e)
        print("Используйте команду get-rate для просмотра доступных валют")

    except ApiRequestError as e:
        print(e)
        print("Повторите попытку позже или проверьте соединение")

    except ValueError as e:
        print(e)
