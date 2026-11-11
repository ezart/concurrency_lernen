import unittest
from concurrent.futures import (
    ThreadPoolExecutor,
    CancelledError,
)
from threading import Event


class TestExecutorShutdown(unittest.TestCase):

    def test_shutdown_cancels_pending_but_not_running_tasks(self):
        started = Event()
        release = Event()

        def task_a():
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Task A was not released")
            return 42

        def task_b():
            return 24

        executor = ThreadPoolExecutor(max_workers=1)

        try:
            future_a = executor.submit(task_a)
            future_b = executor.submit(task_b)

            self.assertTrue(started.wait(timeout=2))

            executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

            # A was already running and must not be cancelled.
            self.assertTrue(future_a.running())
            self.assertFalse(future_a.cancelled())

            # B was queued and should be cancelled.
            self.assertTrue(future_b.cancelled())

            with self.assertRaises(CancelledError):
                future_b.result(timeout=2)

            # Shutdown prevents new submissions.
            with self.assertRaises(RuntimeError):
                executor.submit(lambda: 99)

        finally:
            release.set()
            executor.shutdown(wait=True)

        # A completes successfully despite shutdown.
        self.assertEqual(future_a.result(timeout=2), 42)

    def test_shutdown_without_cancelling_pending_futures(self):
        started = Event()
        release = Event()

        def task_a():
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Task A was not released")
            return "A"

        def task_b():
            return "B"

        executor = ThreadPoolExecutor(max_workers=1)

        try:
            future_a = executor.submit(task_a)
            future_b = executor.submit(task_b)

            self.assertTrue(started.wait(timeout=2))

            executor.shutdown(
                wait=False,
                cancel_futures=False,
            )

            self.assertFalse(future_a.cancelled())
            self.assertFalse(future_b.cancelled())
            self.assertFalse(future_b.done())

        finally:
            release.set()
            executor.shutdown(wait=True)

        self.assertEqual(future_a.result(timeout=2), "A")
        self.assertEqual(future_b.result(timeout=2), "B")

    def test_shutdown_wait_true_waits_for_running_task(self):
        started = Event()
        release = Event()
        shutdown_returned = Event()

        def task():
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Task was not released")
            return 42

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(task)

        def perform_shutdown():
            executor.shutdown(wait=True)
            shutdown_returned.set()

        from threading import Thread

        shutdown_thread = Thread(target=perform_shutdown)

        try:
            self.assertTrue(started.wait(timeout=2))
            shutdown_thread.start()

            # The running task is blocked, so shutdown
            # must not have returned yet.
            self.assertFalse(shutdown_returned.wait(timeout=0.1))

        finally:
            release.set()
            shutdown_thread.join(timeout=5)
            executor.shutdown(wait=True)

        self.assertFalse(shutdown_thread.is_alive())
        self.assertTrue(shutdown_returned.is_set())
        self.assertEqual(future.result(timeout=2), 42)


if __name__ == "__main__":
    unittest.main()
