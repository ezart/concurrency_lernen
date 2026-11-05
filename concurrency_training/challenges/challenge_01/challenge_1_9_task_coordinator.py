from concurrent.futures import ThreadPoolExecutor, Future, as_completed


class TaskCoordinator:
    def __init__(self, max_workers: int):
        if max_workers < 1:
            raise ValueError()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = []

    def submit(self, fn, *args, **kwargs) -> Future:
        future = self._executor.submit(fn, *args, **kwargs)
        self._futures.append(future)
        return future

    def collect(self):
        results = []
        for future in as_completed(self._futures):
            try:
                results.append(("ok", future.result()))
            except Exception as e:
                results.append(("error", e))

        return results

    def cancel(self, future: Future) -> bool:
        return future.cancel()

    def shutdown(self):
        self._executor.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()
