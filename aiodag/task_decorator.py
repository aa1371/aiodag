import asyncio
import inspect
from functools import wraps


def task(afunc, *exogenous_deps):
    """
    Example:

        @task
        async def A():
            pass

        @task
        async def B(val=None):
            pass

        async def main():
            # example 1
            a = A()
            b = B(a)

            # example 2
            a = A()
            # b depends on a, but dependency is explicitly stated in task wrapper, not through `val` param
            b = task(B, a)()

    :param afunc: function that creates an awaitable on invocation
    :param exogenous_deps: awaitable
    :return:
    """
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

            await asyncio.gather(*exogenous_deps)

            return await afunc(**callargs)
        return asyncio.create_task(_inner())
    return wrapper
