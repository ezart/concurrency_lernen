from concurrent.futures import FIRST_EXCEPTION, wait, ThreadPoolExecutor
from threading import Event

a_event = Event()
start_a = Event()
b_event = Event()
start_b = Event()


def task_a():
    start_a.set()
    a_event.wait()
    raise ValueError("Task A failed")


def task_b():
    start_b.set()
    b_event.wait()
    return "Task B succeeded"


with ThreadPoolExecutor(max_workers=2) as executor:
    try:
        futures = [executor.submit(task_a), executor.submit(task_b)]
        assert start_a.wait(timeout=1.0)
        assert start_b.wait(timeout=1.0)

        a_event.set()
        done, not_done = wait(futures, timeout=1.0, return_when=FIRST_EXCEPTION)

        assert futures[0] in done
        assert futures[0].done() == True
        assert futures[1] in not_done
        assert futures[1].done() == False

        try:
            futures[0].result()
            assert False, "Value was not raised"
        except ValueError as e:
            assert str(e) == "Task A failed"

        b_event.set()
        assert futures[1].result() == "Task B succeeded"
        assert futures[1].done() == True

    finally:
        a_event.set()
        b_event.set()
