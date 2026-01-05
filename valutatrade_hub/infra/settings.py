
from pathlib import Path
from typing import Any


class SettingsLoader:


    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self):
 
        self._settings = {
            "DATA_DIR": Path("data"),
            "USERS_FILE": Path("data/users.json"),
            "PORTFOLIOS_FILE": Path("data/portfolios.json"),
            "RATES_FILE": Path("data/rates.json"),

  
            "RATES_TTL_SECONDS": 300,  # 5 минут

         
            "BASE_CURRENCY": "USD",

            
            "LOG_DIR": Path("logs"),
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "%(asctime)s | %(levelname)s | %(message)s",
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def reload(self):

        self._init_settings()
