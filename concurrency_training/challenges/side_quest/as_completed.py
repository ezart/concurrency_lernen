from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

start_a = Event()
start_b = Event()
start_c = Event()
a = Event()
b = Event()
c = Event()


def task_a():
    start_a.set()
    a.wait()
    return "A completed"


def task_b():
    start_b.set()
    b.wait()
    return "B completed"


def task_c():
    start_c.set()
    c.wait()
    return "C completed"


with ThreadPoolExecutor(max_workers=3) as executor:

    try:
        future_a = executor.submit(task_a)
        future_b = executor.submit(task_b)
        future_c = executor.submit(task_c)
        # test whether the three have started
        assert start_a.wait(timeout=1.0)
        assert start_b.wait(timeout=1.0)
        assert start_c.wait(timeout=1.0)
        # release A & B
        #
        futures_as_completed = as_completed([future_a, future_b, future_c], timeout=4.0)
        b.set()

        f = next(futures_as_completed)
        assert future_b == f
        assert f.result(timeout=1.0) == "B completed"

        c.set()
        f = next(futures_as_completed)
        assert future_c == f
        assert f.result(timeout=1.0) == "C completed"

        a.set()
        f = next(futures_as_completed)
        assert future_a == f
        assert f.result(timeout=1.0) == "A completed"

    finally:
        a.set()
        b.set()
        c.set()
