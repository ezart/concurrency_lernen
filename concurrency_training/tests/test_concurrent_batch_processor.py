from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import TestCase
from unittest.mock import patch

from concurrency_training.challenges.side_quest.concurrent_batch_processor import ConcurrentBatchProcessor


class ConcurrentBatchProcessorTest(TestCase):
    def test_independent_tasks_execute_concurrently(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            try:
                # two independent tasks can execute concurently_1
                started_1 = Event()
                started_2 = Event()
                release_1 = Event()
                release_2 = Event()

                def task_1():
                    started_1.set()
                    if not release_1.wait(timeout=5.0):
                        raise TimeoutError("Task 1 not released")
                    return "task 1"

                def task_2():
                    started_2.set()
                    if not release_2.wait(timeout=5.0):
                        raise TimeoutError("Task 2 not released")
                    return "task 2"

                cbp = ConcurrentBatchProcessor(max_workers=2)
                future = executor.submit(cbp.process, {"task_1": task_1, "task_2": task_2})
                self.assertTrue(started_1.wait(timeout=1.0) and started_2.wait(timeout=1.0))

                release_1.set()
                release_2.set()

                self.assertEqual(
                    future.result(timeout=1.0),
                    {
                        "task_1": {"status": "success", "result": "task 1"},
                        "task_2": {"status": "success", "result": "task 2"},
                    },
                )

            finally:
                # clean up
                release_1.set()
                release_2.set()

    def test_results_associated_with_correct_task_ids(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            try:
                # two independent tasks can execute concurently_1
                started_1 = Event()
                started_2 = Event()
                release_1 = Event()
                release_2 = Event()
                task_2_finished = Event()

                def task_1():
                    started_1.set()
                    if not release_1.wait(timeout=5.0):
                        raise TimeoutError("Task 1 not released")
                    return "task 1"

                def task_2():
                    started_2.set()
                    if not release_2.wait(timeout=5.0):
                        raise TimeoutError("Task 2 not released")

                    task_2_finished.set()
                    return "task 2"

                cbp = ConcurrentBatchProcessor(max_workers=2)
                future = executor.submit(cbp.process, {"task_2": task_2, "task_1": task_1})
                self.assertTrue(started_1.wait(timeout=1.0) and started_2.wait(timeout=1.0))

                release_2.set()

                self.assertTrue(
                    task_2_finished.wait(timeout=1.0),
                    "Task 2 did not reach its completion signal",
                )

                release_1.set()

                self.assertEqual(
                    future.result(timeout=1.0),
                    {
                        "task_1": {"status": "success", "result": "task 1"},
                        "task_2": {"status": "success", "result": "task 2"},
                    },
                )

            finally:
                # clean up
                release_1.set()
                release_2.set()

    def test_task_failure_does_not_affect_other_tasks(self):
        expected = {
            "validate_a": {
                "status": "success",
                "result": True,
            },
            "validate_b": {
                "status": "failed",
                "error": "Invalid account",
            },
            "validate_c": {
                "status": "success",
                "result": 100,
            },
        }

        def validate_a():
            return True

        def validate_b():
            raise ValueError("Invalid account")

        def validate_c():
            return 100

        cbp = ConcurrentBatchProcessor(max_workers=3)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(
                cbp.process, {"validate_a": validate_a, "validate_b": validate_b, "validate_c": validate_c}
            )

            result = future.result(timeout=2.0)
            self.assertEqual(result, expected)

    def test_executor_cleanup_on_unexpected_failure(self):
        executor_path = "concurrency_training.challenges.side_quest." "concurrent_batch_processor.ThreadPoolExecutor"

        def task_a():
            return 42

        with patch(executor_path) as mock_executor:
            executor = mock_executor.return_value.__enter__.return_value

            # Simulate an unexpected infrastructure failure
            # while the processor submits work.
            executor.submit.side_effect = RuntimeError("Executor submission failed")

            cbp = ConcurrentBatchProcessor(max_workers=2)

            with self.assertRaisesRegex(
                RuntimeError,
                "Executor submission failed",
            ):
                cbp.process({"task_a": task_a})

            # Verify executor construction.
            mock_executor.assert_called_once_with(max_workers=2)

            # Verify entry into the context manager.
            mock_executor.return_value.__enter__.assert_called_once()

            # Verify cleanup even though submission failed.
            mock_executor.return_value.__exit__.assert_called_once()
