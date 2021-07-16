import asyncio
from aiodag import task


@task
async def processA():
    await asyncio.sleep(1)
    print('Done processA')

async def processB():
    await asyncio.sleep(5)
    print('Done processB')

@task
async def processC():
    await asyncio.sleep(1)
    print('Done processC')

@task
async def processD(f):
    await asyncio.sleep(f / 2)
    print('Done processD')

@task
async def processE():
    await asyncio.sleep(1)
    print('Done processE')

@task
async def processF():
    val = 2
    await asyncio.sleep(val)
    print('Done processF')
    return val


async def main():
    # ok to redecorate tasks
    # pass explicit dependencies to the task decorator
    # these are explicit because they are not implied through the func params
    tF = processF()
    tE = processE()
    tD = task(processD, tE)(tF)  # you can see this one has endogenous and exogenous deps
    tC = task(processC, tD)()
    tB = task(processB, tE)()
    tA = task(processA, tB, tC)()
    await asyncio.gather(tA)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
