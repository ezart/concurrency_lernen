from concurrent.futures import ThreadPoolExecutor, Future


class TaskRunner:
    def __init__(self, max_workers: int):
        if max_workers < 1:
            raise ValueError("No. of maximum workers should be more than 0")

        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def __enter__(self):
        print("Starting Task Runner ...")
        return self

    def __exit__(self, exc_type, exc, tb):
        print("Shutting down and cleaning up resources...")
        self.executor.shutdown()

    def submit(self, fn, *args, **kwargs) -> Future:
        future = self.executor.submit(fn, *args, **kwargs)
        return future

    def shutdown(self):
        self.executor.shutdown()
