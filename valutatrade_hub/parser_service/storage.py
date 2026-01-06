import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict

from .config import ParserConfig


class RatesStorage:
    def __init__(self, config: ParserConfig):
        # Пути к файлам
        self.rates_path = Path(config.RATES_FILE_PATH)
        self.history_path = Path(config.HISTORY_FILE_PATH)


    def _load_snapshot(self) -> dict:
        if not self.rates_path.exists():
            return {"pairs": {}, "last_refresh": None}

        text = self.rates_path.read_text(encoding="utf-8").strip()
        if not text:
            return {"pairs": {}, "last_refresh": None}

        return json.loads(text)

    def _save_snapshot(self, data: dict) -> None:
        self.rates_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.rates_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.rates_path)

    def update_snapshot(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        source: str,
        timestamp: str | None = None,
    ) -> None:
        snapshot = self._load_snapshot()

        pair_key = f"{from_currency}_{to_currency}"
        now = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        current = snapshot["pairs"].get(pair_key)
        if current:
            if current["updated_at"] >= now:
                return  # не обновляем более старым значением

        snapshot["pairs"][pair_key] = {
            "rate": rate,
            "updated_at": now,
            "source": source,
        }
        snapshot["last_refresh"] = now

        self._save_snapshot(snapshot)

    def get_last_refresh(self) -> str | None:
        snapshot = self._load_snapshot()
        return snapshot.get("last_refresh")


    def append_history(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        source: str,
    ) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        history = []
        if self.history_path.exists():
            text = self.history_path.read_text(encoding="utf-8").strip()
            if text:
                history = json.loads(text)

        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record_id = f"{from_currency}_{to_currency}_{timestamp}"

        history.append(
            {
                "id": record_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
            }
        )

        tmp = self.history_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.history_path)

