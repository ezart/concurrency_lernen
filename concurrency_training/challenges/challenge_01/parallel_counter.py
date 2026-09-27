from multiprocessing import Lock, Value


class ParallelCounter:
    counter = 0
    lock = Lock()

    def __init__(self, initial_value: int = 0):
        self.counter = Value("i", initial_value)

    def increment(self, amount: int = 1) -> None:
        with self.lock:
            counter += amount

    def value(self) -> int:
        with self.lock:
            return self.counter
