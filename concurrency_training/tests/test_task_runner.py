from concurrent.futures import Future
import threading
import unittest
from unittest.mock import MagicMock
from challenges.challenge_01.task_runner import TaskRunner


class TaskRunnerTest(unittest.TestCase):
    def test_invalid_max_workers(self):
        with self.assertRaises(ValueError):
            runner = TaskRunner(max_workers=0)

    def test_submit_returns_future(self):
        runner = TaskRunner(max_workers=3)
        self.assertIsInstance(runner.submit(pow, 2, 3), Future)

    def test_task_executes(self):
        mock_func = MagicMock()

        runner = TaskRunner(max_workers=1)
        future = runner.submit(mock_func)
        future.result()  # wait for task to complete
        mock_func.assert_called_once_with()

    def test_arguments_and_keyword_arguments_work(self):
        mock_func = MagicMock()

        runner = TaskRunner(max_workers=1)
        future = runner.submit(mock_func, 2, 3, 4, name="Ford Prefect", greeting="Hello")
        future.result()
        mock_func.assert_called_once_with(2, 3, 4, name="Ford Prefect", greeting="Hello")

    def test_multiple_task_execute_concurrently(self):
        # should uses only one worker, the test may hang until the test process is interrupted
        # Add timeout to make failures controlled
        barrier = threading.Barrier(4, timeout=2)
        runner = TaskRunner(max_workers=4)

        def task_1(thread_ID: int, barrier: threading.Barrier):
            print("task id: ", thread_ID, " has reached the barrier and is waiting ...\n")
            barrier.wait()
            print(f"task: {thread_ID} done")

        def task_2(thread_ID: int, barrier: threading.Barrier):
            print("task id: ", thread_ID, " has reached the barrier and is waiting ...\n")
            barrier.wait()
            print(f"task: {thread_ID} done")

        futures = [
            runner.submit(fn=task_1, thread_ID=1, barrier=barrier),
            runner.submit(fn=task_2, thread_ID=2, barrier=barrier),
            runner.submit(fn=task_1, thread_ID=3, barrier=barrier),
            runner.submit(fn=task_2, thread_ID=4, barrier=barrier),
        ]
        for future in futures:
            future.result()
        self.assertTrue(all(future.done() for future in futures))
        self.assertEqual(barrier.n_waiting, 0)

    def test_exceptions_propagate_through_future_results(self):
        def side_effect(n: int) -> int:
            if n % 2 == 0:
                return n
            raise ValueError("Odd number detected")

        mock = MagicMock(side_effect=side_effect)

        runner = TaskRunner(max_workers=4)

        futures = [runner.submit(mock, i) for i in range(1, 10)]

        for i in range(0, len(futures)):
            print("\n\n", i)
            if (i + 1) % 2 != 0:
                with self.assertRaises(ValueError) as context:
                    futures[i].result()
                self.assertEqual(str(context.exception), "Odd number detected")
            else:
                self.assertEqual(futures[i].result(), i + 1)

    def test_shutdown_prevents_new_submisions(self):
        runner = TaskRunner(max_workers=2)
        self.assertEqual(runner.submit(pow, 2, 3).result(), 8)

        runner.shutdown()

        with self.assertRaises(RuntimeError):
            runner.submit(pow, 2, 3)
