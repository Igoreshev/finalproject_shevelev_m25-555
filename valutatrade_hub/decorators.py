
from functools import wraps
from datetime import datetime
from valutatrade_hub.logging_config import setup_logging

logger = setup_logging()


def log_action(action: str, verbose: bool = False):

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            currency = None
            amount = None

            if len(args) >= 1:
                currency = args[0]
            if len(args) >= 2:
                amount = args[1]

            try:
                result = func(*args, **kwargs)

                logger.info(
                    f"{action} currency='{currency}' "
                    f"amount={amount} result=OK"
                )

                return result

            except Exception as e:
                logger.info(
                    f"{action} currency='{currency}' "
                    f"amount={amount} result=ERROR "
                    f"error_type={type(e).__name__} "
                    f"error_message='{e}'"
                )
                raise  # пробрасываем дальше

        return wrapper

    return decorator
