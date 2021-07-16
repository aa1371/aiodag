import asyncio
import inspect
from functools import wraps


def task(afunc):
    @wraps(afunc)
    def wrapper(*args, **kwargs):
        async def _inner():
            callargs = inspect.signature(afunc).bind(*args, **kwargs).arguments
            gather_args = {}
            non_gather_args = {}
            for k, v in callargs.items():
                if inspect.isawaitable(v):
                    gather_args[k] = v
                else:
                    non_gather_args[k] = v

            gather_args = dict(
                zip(
                    gather_args.keys(),
                    await asyncio.gather(*gather_args.values())
                )
            )

            callargs = {**gather_args, **non_gather_args}
            return await afunc(**callargs)
        return asyncio.create_task(_inner())
    return wrapper
