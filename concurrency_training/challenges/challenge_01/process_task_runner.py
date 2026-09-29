from multiprocessing import Lock
from concurrent.futures import ProcessPoolExecutor, Future

from collections.abc import Iterable


class ProcessTaskRunner:
    """
    max_workers must be greater than zero.
    submit() executes a function in a worker process and returns a Future.
    Function arguments must be passed correctly.
    Multiple submitted tasks should execute concurrently.
    Exceptions raised inside workers must become observable through Future.result().
    map() should distribute work across the process pool.
    shutdown() must prevent new submissions.
    Use one persistent ProcessPoolExecutor. Don't create a new executor for every task.
    Don't use multiprocessing.Manager.
    Don't use threads to implement the runner
    """

    def __init__(self, max_workers: int):
        if max_workers < 1:
            raise ValueError("Max workers must be greater than zero")
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

    def submit(self, fn, *args, **kwargs) -> Future:
        return self._executor.submit(fn, *args, **kwargs)

    def map(self, fn, iterable: Iterable):
        return self._executor.map(fn, iterable)

    def shutdown(self):
        self._executor.shutdown()

    def __enter__(self):
        print("\n\n\n ****starting Process Task Runner ... ****\n\n\n")
        return self

    def __exit__(self, exc_type, exc, tb):
        print(f"exiting Proces Task Runner")
        self._executor.shutdown()
