import asyncio
import inspect
from functools import wraps


def task(afunc):
    @wraps(afunc)
    def wrapper(*args):  # TODO: support *args and **kwargs
        async def _inner():
            nonlocal args
            args = [arg if inspect.isawaitable(arg) else _task_wrapper(arg)
                    for arg in args]
            args = await asyncio.gather(*args)
            return await afunc(*args)
        return asyncio.create_task(_inner())
    return wrapper


async def _task_wrapper(val):
    return val
