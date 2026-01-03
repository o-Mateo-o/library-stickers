import shutil
from functools import update_wrapper
from pathlib import Path
from typing import Callable, TypeVar

from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


def with_temp_dir(temp_dir: Path) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Ensures temp_dir exists before function execution
    and clears its contents after execution.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            temp_dir.mkdir(parents=True, exist_ok=True)
            try:
                return func(*args, **kwargs)
            finally:
                for item in temp_dir.iterdir():
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)

        return update_wrapper(wrapper, func)

    return decorator
