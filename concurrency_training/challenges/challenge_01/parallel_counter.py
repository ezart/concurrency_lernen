from multiprocessing import Lock, Value


class ParallelCounter:

    def __init__(self, initial_value: int = 0):
        self._counter = Value("i", initial_value)
        self._lock = Lock()

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._counter.value += amount

    def value(self) -> int:
        with self._lock:
            return self._counter.value
