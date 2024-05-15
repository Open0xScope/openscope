#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 19:01
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : utils.py.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
import datetime
import re
import time
from functools import wraps
from time import sleep
from typing import Any, Callable, Literal, ParamSpec, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

P = ParamSpec("P")
R = TypeVar("R")


def timeit(func: Callable[P, R]):
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        log(f"Execution time of {func.__name__}: {execution_time:.6f} seconds")
        return result

    return wrapper


def iso_timestamp_now() -> str:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    iso_now = now.isoformat()
    return iso_now


def log(
        msg: str,
        *values: object,
        sep: str | None = " ",
        end: str | None = "\n",
        file: Any | None = None,
        flush: Literal[False] = False
):
    print(f"[{iso_timestamp_now()}] " + msg, *values, sep=sep, end=end, file=file, flush=flush)


def is_ethereum_address(address: str) -> bool:
    pattern = re.compile(r"^0x[a-fA-F0-9]{40}$")
    return bool(pattern.match(address))


def main():
    pass


if __name__ == '__main__':
    main()
