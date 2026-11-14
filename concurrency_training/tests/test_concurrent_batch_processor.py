from concurrent.futures import ThreadPoolExecutor
import threading
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

    # TEST 5 — Parallel banking service calls
    def test_parallel_banking_service_lookups(self):
        """
        Simulate independent balance, customer profile,
        and loan eligibility service calls.

        All three must start before any is released.
        """
        started = {name: threading.Event() for name in ("balance", "profile", "loan")}
        release = threading.Event()

        def service_call(name, response):
            def execute():
                started[name].set()

                if not release.wait(timeout=5):
                    raise TimeoutError(f"{name} service was not released")

                return response

            return execute

        tasks = {
            "balance": service_call("balance", {"currency": "KES", "available": 12500}),
            "profile": service_call("profile", {"customer_id": "C102", "kyc": "verified"}),
            "loan": service_call("loan", {"eligible": True, "limit": 50000}),
        }

        processor = ConcurrentBatchProcessor(max_workers=3)

        with ThreadPoolExecutor(max_workers=1) as runner:
            future = runner.submit(processor.process, tasks)

            try:
                for name, event in started.items():
                    self.assertTrue(
                        event.wait(timeout=2),
                        f"{name} did not start concurrently",
                    )
            finally:
                release.set()

            results = future.result(timeout=2)

        self.assertEqual(
            results,
            {
                "balance": {
                    "status": "success",
                    "result": {"currency": "KES", "available": 12500},
                },
                "profile": {
                    "status": "success",
                    "result": {"customer_id": "C102", "kyc": "verified"},
                },
                "loan": {
                    "status": "success",
                    "result": {"eligible": True, "limit": 50000},
                },
            },
        )

    # TEST 6 — Partial failure in a payment reconciliation batch
    def test_payment_reconciliation_partial_failure(self):
        """
        One invalid transaction must not prevent valid
        transactions from being reconciled.
        """
        transactions = {
            "TXN-001": {"amount": 1500, "currency": "KES"},
            "TXN-002": {"amount": -200, "currency": "KES"},
            "TXN-003": {"amount": 8500, "currency": "KES"},
            "TXN-004": {"amount": 0, "currency": "KES"},
        }

        def reconcile(transaction_id, transaction):
            def execute():
                amount = transaction["amount"]

                if amount <= 0:
                    raise ValueError(f"Invalid amount for {transaction_id}")

                return {
                    "transaction_id": transaction_id,
                    "reconciled_amount": amount,
                }

            return execute

        tasks = {
            transaction_id: reconcile(transaction_id, transaction)
            for transaction_id, transaction in transactions.items()
        }

        processor = ConcurrentBatchProcessor(max_workers=2)
        results = processor.process(tasks)

        self.assertEqual(
            results,
            {
                "TXN-001": {
                    "status": "success",
                    "result": {
                        "transaction_id": "TXN-001",
                        "reconciled_amount": 1500,
                    },
                },
                "TXN-002": {
                    "status": "failed",
                    "error": "Invalid amount for TXN-002",
                },
                "TXN-003": {
                    "status": "success",
                    "result": {
                        "transaction_id": "TXN-003",
                        "reconciled_amount": 8500,
                    },
                },
                "TXN-004": {
                    "status": "failed",
                    "error": "Invalid amount for TXN-004",
                },
            },
        )

    # TEST 7 — Maximum worker concurrency
    def test_batch_never_exceeds_max_workers(self):
        """
        Simulate six independent report-generation jobs.

        With max_workers=2, no more than two tasks may
        be executing simultaneously.
        """
        lock = threading.Lock()
        release = threading.Event()
        two_started = threading.Event()

        active = 0
        peak_active = 0

        def generate_report(report_id):
            def execute():
                nonlocal active, peak_active

                with lock:
                    active += 1
                    peak_active = max(peak_active, active)

                    if active == 2:
                        two_started.set()

                try:
                    if not release.wait(timeout=5):
                        raise TimeoutError("Report generation not released")

                    return f"report-{report_id}.pdf"
                finally:
                    with lock:
                        active -= 1

            return execute

        tasks = {f"report_{i}": generate_report(i) for i in range(6)}

        processor = ConcurrentBatchProcessor(max_workers=2)

        with ThreadPoolExecutor(max_workers=1) as runner:
            future = runner.submit(processor.process, tasks)

            try:
                self.assertTrue(
                    two_started.wait(timeout=2),
                    "Two workers did not become active",
                )
            finally:
                release.set()

            results = future.result(timeout=2)

        self.assertEqual(peak_active, 2)
        self.assertEqual(len(results), 6)

        for i in range(6):
            self.assertEqual(
                results[f"report_{i}"],
                {
                    "status": "success",
                    "result": f"report-{i}.pdf",
                },
            )

    # TEST 8 — Processor reuse across independent batches
    def test_processor_can_process_multiple_independent_batches(self):
        """
        Simulate reusing a processor for two successive
        settlement batches.

        Results must not leak between batches.
        """
        processor = ConcurrentBatchProcessor(max_workers=2)

        morning_results = processor.process(
            {
                "morning_settlement": lambda: {
                    "batch": "AM",
                    "total": 150000,
                },
            }
        )

        evening_results = processor.process(
            {
                "evening_settlement": lambda: {
                    "batch": "PM",
                    "total": 275000,
                },
            }
        )

        self.assertEqual(
            morning_results,
            {
                "morning_settlement": {
                    "status": "success",
                    "result": {"batch": "AM", "total": 150000},
                },
            },
        )

        self.assertEqual(
            evening_results,
            {
                "evening_settlement": {
                    "status": "success",
                    "result": {"batch": "PM", "total": 275000},
                },
            },
        )

        self.assertNotIn("morning_settlement", evening_results)
        self.assertNotIn("evening_settlement", morning_results)

    # TEST 9 — Empty batch and no-op processing
    def test_empty_batch_returns_empty_results(self):
        """
        Simulate a scheduled reconciliation job that
        finds no transactions to process.
        """
        processor = ConcurrentBatchProcessor(max_workers=4)

        results = processor.process({})

        self.assertEqual(results, {})
        self.assertIsInstance(results, dict)

        # The same processor must remain usable afterward.
        subsequent_results = processor.process(
            {
                "health_check": lambda: "healthy",
            }
        )

        self.assertEqual(
            subsequent_results,
            {
                "health_check": {
                    "status": "success",
                    "result": "healthy",
                },
            },
        )
