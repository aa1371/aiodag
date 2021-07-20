import asyncio
import inspect
from functools import wraps


def task(afunc=None, *exogenous_deps, raw=False):
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

    :param afunc: callable that creates an awaitable on invocation
    :param exogenous_deps: awaitable
    :param raw: bool
        if True, will wait on deps rather than gather, and pass task objects
        to afunc, rather than resolved task results
    :return:
    """
    if raw and exogenous_deps:
        # TODO: if raw=True, provide a way to pass exog deps to task, then can
        #  have exog deps with raw=True
        raise ValueError('Cannot have exogenous dependencies on a raw task.')

    def _decorate(wrapped_afunc):  # this layer is to allow `@task` or `@task(raw=True)`
        @wraps(wrapped_afunc)
        def wrapper(*args, **kwargs):
            async def _inner():
                callargs = inspect.signature(wrapped_afunc).bind(*args, **kwargs).arguments
                if raw:
                    for k, v in callargs.items():
                        if not inspect.isawaitable(v):
                            callargs[k] = asyncio.create_task(_task_wrapper(v))
                    if callargs:
                        await asyncio.wait(callargs.values())
                else:
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

                if exogenous_deps:
                    await asyncio.wait(exogenous_deps)

                return await wrapped_afunc(**callargs)
            return asyncio.create_task(_inner())
        return wrapper

    if afunc:
        return _decorate(afunc)

    return _decorate


async def _task_wrapper(val):
    return val
