import asyncio
from aiodag import task


# timings here defined to demo obvious expected
# async behavior in completion order of print statements
SLEEP_TIMES = {
    'a1': 1,
    'a2': 2,
    'b1': 4,
    'b2': 0.5,
    'c1': 6,
    'c2': 3.5
}


@task
async def fetch(x, i):
    await asyncio.sleep(SLEEP_TIMES[x])
    ret_val = f'f({x})'
    print(f'Done {ret_val}', i)
    return ret_val


@task
async def process(x1, x2, i):
    await asyncio.sleep(1)
    ret_val = f'p({x1}, {x2})'
    print(f'Done {ret_val}', i)
    return ret_val


async def process_undecorated(x1, x2, i):
    await asyncio.sleep(1)
    ret_val = f'p({x1}, {x2})'
    print(f'Done {ret_val}', i)
    return ret_val


async def main1():
    fa1 = fetch('a1', 0)
    fa2 = fetch('a2', 0)
    fb1 = fetch('b1', 0)
    fb2 = fetch('b2', 0)
    fc1 = fetch('c1', 0)
    fc2 = fetch('c2', 0)
    pa = process(fa1, fa2, 0)
    pb = process(fb1, fb2, 0)
    pc = process(fc1, fc2, 0)
    pax = process(fa1, fa2, 1)
    return await asyncio.gather(pa, pb, pc, pax)


async def main2():
    i = 0
    while i < 10:
        fa1 = fetch('a1', i)
        fa2 = fetch('a2', i)
        fb1 = fetch('b1', i)
        fb2 = fetch('b2', i)
        fc1 = fetch('c1', i)
        fc2 = fetch('c2', i)
        pa = task(process)(fa1, fa2, i)
        pb = task(process)(fb1, fb2, i)
        pc = task(process)(fc1, fc2, i)
        await asyncio.sleep(2)
        i += 1


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    print('Example 1')
    loop.run_until_complete(main1())

    print('Example 2')
    loop.run_until_complete(main2())
