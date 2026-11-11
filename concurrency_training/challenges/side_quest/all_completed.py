from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
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
    raise ValueError("B failed")


def task_c():
    start_c.set()
    c.wait()
    return "C completed"


with ThreadPoolExecutor(max_workers=3) as executor:
    future_a = executor.submit(task_a)
    future_b = executor.submit(task_b)
    future_c = executor.submit(task_c)

    try:
        # test whether the three have started
        assert start_a.wait(timeout=1.0)
        assert start_b.wait(timeout=1.0)
        assert start_c.wait(timeout=1.0)
        # release A & B
        a.set()
        b.set()

        done, not_done = wait([future_a, future_b, future_c], timeout=1.0, return_when=ALL_COMPLETED)

        assert future_a in done
        assert future_a.done() == True
        assert future_b in done
        assert future_b.done() == True
        assert future_c in not_done
        assert future_c.done() == False

        c.set()

        done, not_done = wait([future_a, future_b, future_c], timeout=1.0, return_when=ALL_COMPLETED)

        assert future_a in done
        assert future_a.done() == True
        assert future_b in done
        assert future_b.done() == True
        assert future_c in done
        assert future_c.done() == True

        assert future_a.result() == "A completed"
        assert future_c.result() == "C completed"

        try:
            future_b.result(timeout=1.0)
        except ValueError as e:
            assert str(e) == "B failed"
        else:
            assert False, "Exception not raised"

    finally:
        a.set()
        b.set()
        c.set()
