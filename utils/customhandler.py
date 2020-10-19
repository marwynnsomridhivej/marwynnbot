import functools
from typing import Tuple


def handle(*exceptions: Tuple[Exception], to_raise: Exception = None):
    def actual_deco(func):
        @functools.wraps(func)
        async def handler(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (exceptions):
                if to_raise:
                    raise to_raise
        return handler
    return actual_deco