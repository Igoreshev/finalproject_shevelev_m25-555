
from typing import List
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from .api_clients import BaseApiClient
from .storage import RatesStorage


class RatesUpdater:
    def __init__(
        self,
        clients: List[BaseApiClient],
        storage: RatesStorage,
    ):
        self.clients = clients
        self.storage = storage

    def run_update(self) -> int:
        print("Старт обновления курсов")

        total_updated = 0
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        for client in self.clients:
            client_name = client.__class__.__name__
            print(f"Запрос к {client_name}")

            try:
                rates = client.fetch_rates()
                print(f"{client_name}: получено {len(rates)} курсов")

                for pair_key, rate in rates.items():
                    from_currency, to_currency = pair_key.split("_")

                    # обновляем snapshot
                    self.storage.update_snapshot(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        source=client_name,
                        timestamp=now,
                    )

                    # пишем историю
                    self.storage.append_history(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        source=client_name,
                    )

                    total_updated += 1

            except ApiRequestError as e:
                print(f"Ошибка при запросе к {client_name}: {e}")
            except Exception as e:
                print(f"Неожиданная ошибка в {client_name}: {e}")

        print(f"Обновление завершено ({total_updated} пар)")
        return total_updated
