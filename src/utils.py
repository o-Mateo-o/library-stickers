import shutil
from functools import update_wrapper, wraps
from pathlib import Path
from typing import Callable, ParamSpec, Type, TypeVar

from typing_extensions import ParamSpec


class AppError(Exception): ...


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


def arg_tuple_not_none(func: Callable[P, bool]) -> Callable[P, bool]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        if len(args) < 2 or not isinstance(args[1], tuple):
            raise TypeError("Expected an instance method with one tuple argument")

        if any(x is None for x in args[1]):
            return False

        return func(*args, **kwargs)

    return wrapper


def errordialog(
    *exceptions: Type[Exception],
) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """
    Decorator that catches the specified exceptions from the decorated function
    and calls `parent.show_error(message)`.

    Assumes the first argument (`parent`) has a `show_error(str)` method.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
            if not args:
                raise TypeError(
                    "Expected the first argument to be 'parent' with show_error method"
                )
            parent = args[0]
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # type ignore because we trust parent has show_error
                parent.show_error(str(e))  # type: ignore[attr-defined]
                return None
            except Exception as e:
                parent.show_error(f"Niezidentyfikowany błąd: {str(e)}")  # type: ignore[attr-defined]
                return None

        return wrapper

    return decorator
