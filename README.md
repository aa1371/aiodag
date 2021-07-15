# aiodag
Build and execute AsyncIO powered DAGs

aiodag allows you to easily define complex asynnchronous processing pipelines by treating the pipeline as a DAG consisting of a collection of independent tasks. Rather than being connected through static source code definitions, or complicated plumbing code, these tasks are connected through a functional invocation interface that feels like you're writing synchronous code.

The entire API consists of a single decorator called `task`, that you can either add directly on the async function definitions, or invoke at execution time. The library very lightweight, depending only on the python standard library.

Let's start with an example of a simple ETL pipeline.
In the section below we will define all the independent tasks for our pipeline. You'll see that each task definition knows nothing about any of the other task definitions.
```
from aiodag import task

@task
async def fetch(some_id):
    # sleep times here are solely to make the async behavior obvious from the printout order
    sleep_time = {
        'a1': 1, 'a2': 2, 'b1': 4, 'b2': 0.5, 'c1': 6, 'c2': 3.5
    }[some_id]
    await asyncio.sleep(sleep_time)
    ret_val = some_id + 'x'
    print(f'Fetched {some_id}')
    return ret_val
    

@task
async def concatenate(pair_item1, pair_item2):
    """
    Imagine this function sends the pair of items to a third-party
    service to do the concatenation, hence the need for async.
    """
    await asyncio.sleep(1)
    ret_val = pair_item1 + pair_item2
    print(f'Concated {(pair_item1, pair_item2)}')
    return ret_val
    
    
# notice we didn't decorate this coroutine, we can still hook this up to the framework
# in the next section when we build and invoke our pipeline we will show how to do that
# this is useful in cases where you can't or don't want to decorate your coroutine
async def strip_numbers(alpha_num_string):
    """
    Again, imagine some unneccesary service to perform this strip
    """
    await asyncio.sleep(1)
    ret_val = ''.join(x for x in alpha_num_string if not x.isdigit())
    print(f'Stripped {alpha_num_string}')
    return ret_val


@task
async def upload(a_data, b_data, c_data):
    await asyncio.sleep(1)
    print(f'''
        Uploaded data:
        {a_data}
        {b_data}
        {c_data}
    ''')

```
Now let's build and execute our pipeline
```
import asyncio

async def main():
    fa1 = fetch('a1')
    fa2 = fetch('a2')
    fb1 = fetch('b1')
    fb2 = fetch('b2')
    fc1 = fetch('c1')
    fc2 = fetch('c2')
    
    ca = concatenate(fa1, fa2)
    cb = concatenate(fb1, fb2)
    cc = concatenate(fc1, fc2)
    
    cab = concatenate(ca, cb)
    
    # see below that we can call the task decorator at invocation time
    # if our coroutine wasn't decorated to begin with
    sa = task(strip_numbers)(ca)  # notice that we are/can reuse a task result in more than one place
    sab = task(strip_numbers)(cab)
    sc = task(strip_numbers)(cc)

    upload(sa, sab, sc)
    
    # put this here so loop.run_until_complete doesn't finish prematurely
    await asyncio.sleep(10)
    
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
```

You can see from the print outs that our pipeline tasks were executed asynchronously and in the optimal runtime. You might have also noticed that we never awaited or gathered any of our tasks, that is because each invocation of a task is implicitly scheduled on the event loop. However, we can still await/gather the results of the task invocations if we want. Behind the scenes what's happening is the following DAG is built and optimally executed.

![alt text](https://github.com/aa1371/aiodag/blob/main/assets/PipelineDAG.png?raw=true)

If the above example feels a bit too static, don't worry, you can make these invocations and add new tasks dynamically throughout the lifetime of your eventloop. See the simple contrived example below:

```
import time

async def main():
    start_time = time.time()
    while True:
        if round(time.time() - start_time) % 2 == 0:
            concatenate(fetch('a1'), fetch('a2'))
        else:
            concatenate(fetch('b1'), fetch('b2'))
        if time.time() - start_time > 10:
            break
        await asyncio.sleep(0.5)
        
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
```





