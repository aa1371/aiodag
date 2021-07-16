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
    # we could also have just gathered the result of upload,
    # but refrained from doing so to demonstrate that the task
    # would still be executed if you didn't
    await asyncio.sleep(10)
    
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
```

You can see from the print outs that our pipeline tasks were executed asynchronously and in the optimal runtime. You might have also noticed that we never awaited or gathered any of our tasks, that is because each invocation of a task is implicitly scheduled on the event loop. However, we can still await/gather the results of the task invocations if we want. One last thing to note is that some tasks took in the result of another task (e.g. concatenate calls) and some just took in a "plain" value (e.g. fetch calls). Task parameters can be anything, if it is the result of another task it will make sure to resolve the task before passing the value through, if it is something else, it will just treat it like a regular function parameter.

Behind the scenes what's happening is the following DAG is built and optimally executed.

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

## Endogenous vs Exogenous Depedencies

So far all dependencies we have seen have been implied by and passed through the parameters of an async function. In aiodag we refer to these as `endogenous` dependencies because they are inherent to the task through the function definition. 

However, what if we wanted to apply a dependency to a task that wasn't explicitly part of the task function definition. At invocation time we can define arbitrary extra dependencies on any task, the results of these dependencies will not be passed to the dependent task, but it will still wait for the dependencies to finish before executing the task. We refer to these as `exogenous` dependencies because they are defined externally to and without regard for the context of a task.

You can see how we can define and mix both kinds of dependencies below.

```
import asyncio
from aiodag import task
import time

@task
async def start_after_x_seconds(x):
    await asyncio.sleep(x)

@task
async def fetch():
    print(f'Fetched after {time.time() - START_TIME} secs')
    return 'data'
    
@task
async def process(raw_data):
    await asyncio.sleep(1)
    print(f'Processed after {time.time() - START_TIME} secs')
    return 'processed_' + raw_data
    
async def main():
    fetch_wait = start_after_x_seconds(2)
    process_wait = start_after_x_seconds(4)
    
    f = task(fetch, fetch_wait)()
    p = task(process, process_wait)(f)
    return await asyncio.gather(p)
    
START_TIME = time.time()
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
```

As you can see in the above example `fetch` takes no parameters, thus it has no endogenous dependencies. However, you can see that we were still able to apply a dependency through an exogenous dependency passed to the `task` wrapper. Thus, `fetch` will wait to run until the dependency finishes. You can also see in the invocation of process, that we can mix endogenous and exogenous dependencies. One last thing to note is that in order to apply exogenous dependencies we need to explicitly wrap the function with `task` on invocation, which means you might be double wrapping tasks which have already been decorated, this is ok, and will not cause any issues.
