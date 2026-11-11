from concurrent.futures import ThreadPoolExecutor
from threading import Event

started = Event()
release = Event()


def task():
    started.set()
    release.wait()
    return 42


with ThreadPoolExecutor(max_workers=1) as executor:
    try:
        future = executor.submit(task)
        assert started.wait(timeout=1.0), "task not started"

        # attempt to cancel the future
        assert future.cancel() == False, "running task was cancelled"
        assert not future.cancelled()
        assert future.running()
        # release the task
        release.set()
        assert future.result(timeout=1.0) == 42
    finally:
        release.set()
