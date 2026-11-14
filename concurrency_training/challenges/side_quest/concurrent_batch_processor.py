from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


class ConcurrentBatchProcessor:
    """
    Concurrency: Execute independent tasks concurrently, respecting max_workers.
    Results: Associate each outcome with its task ID, regardless of completion order.
    Exception isolation: One task raising an exception must not prevent successful tasks from completing.
    Lifecycle: Properly shut down the executor, including when unexpected errors occur.
    Determinism: Tests must not depend on arbitrary sleep() calls.
    """

    def __init__(self, max_workers: int):
        if isinstance(max_workers, bool):
            raise TypeError("max_workers cannot be a boolean")
        if not isinstance(max_workers, int):
            raise TypeError("max_workers must be an integer")
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self.max_workers = max_workers

    def process(self, tasks: dict[str, Callable]) -> dict[str, dict]:
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as e:
            futures = {e.submit(v): k for k, v in tasks.items()}
            tasks_as_completed = as_completed(futures.keys())

            for f in tasks_as_completed:
                try:
                    task_id = futures[f]
                    res = f.result()
                    results[task_id] = {"status": "success", "result": res}
                except Exception as e:
                    task_id = futures[f]
                    results[task_id] = {"status": "failed", "error": str(e)}

        return results
