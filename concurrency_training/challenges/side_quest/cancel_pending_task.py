from concurrent.futures import ThreadPoolExecutor, CancelledError
from threading import Event

started = Event()
release = Event()
started_2 = Event()


def task_1():
    started.set()
    release.wait()
    return "What is the meaning of life?"


def task_2():
    started_2.set()
    return 42


with ThreadPoolExecutor(max_workers=1) as executor:
    try:
        future_1 = executor.submit(task_1)
        future_2 = executor.submit(task_2)

        # check that task 1 started
        assert started.wait(timeout=1.0)
        assert future_1.running()
        assert not future_1.done()

        assert not future_2.running()
        # cancel task 2
        assert future_2.cancel() is True
        assert future_2.cancelled()

        # release task 1
        release.set()
        assert future_1.result(timeout=1.0) == "What is the meaning of life?"

        assert not started_2.wait(timeout=1.0)
        try:
            future_2.result()
            assert False, "Task 2 not cancelled, but completed"
        except CancelledError as e:
            assert True

    finally:
        release.set()
