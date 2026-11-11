import threading
from concurrent.futures import ThreadPoolExecutor
import unittest

event_1 = threading.Event()
event_2 = threading.Event()


def task():
    event_1.set()
    event_2.wait(timeout=1.0)
    return 42


with ThreadPoolExecutor() as executor:
    future = executor.submit(task)

    try:

        assert event_1.wait(timeout=1.0), "Synchronization failure"
        assert future.running() is True
        assert future.done() is False

        event_2.set()

        result = future.result(timeout=1.0)
        assert future.done() is True
        assert result == 42
    finally:
        event_1.set()
        event_2.set()
