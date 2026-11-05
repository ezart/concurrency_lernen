import threading
from concurrent.futures import ThreadPoolExecutor

from unittest import TestCase
from unittest.mock import MagicMock

from challenges.challenge_01.challenge_1_10_DependencyScheduler import DependencyScheduler, DependencyError


class ConcurrencyTracker:
    def __init__(self):
        self.current_running = 0
        self.max_observed = 0
        self.lock = threading.Lock()

    def wrap_task(self, fn):
        """Returns a wrapped version of the task function that tracks active execution count"""

        def wrapper(*args, **kwargs):
            with self.lock:
                self.current_running += 1
                if self.current_running > self.max_observed:
                    self.max_observed = self.current_running

            try:
                return fn(*args, **kwargs)
            finally:
                with self.lock:
                    self.current_running -= 1

        return wrapper


class TestDependencyScheduler(TestCase):
    """

    test_cancel
    """

    def test_invalid_max_workers(self):
        with self.assertRaises(ValueError):
            DependencyScheduler(max_workers=0)
        with self.assertRaises(ValueError):
            DependencyScheduler(max_workers=-1)

    def test_add_task(self):
        scheduler = DependencyScheduler(1)
        scheduler.add_task(task_id="A", fn=print)

        self.assertIn("A", scheduler.task_ids)

    def test_duplicate_task_id(self):
        scheduler = DependencyScheduler(2)
        scheduler.add_task(task_id="A", fn=print)

        with self.assertRaises(ValueError):
            scheduler.add_task(task_id="A", fn=pow, args=[1, 2])

    def test_missing_dependency(self):
        scheduler = DependencyScheduler(2)
        scheduler.add_task(task_id="A", fn=print)
        scheduler.add_task(task_id="B", fn=pow, args=[1, 2], depends_on=["C"])
        with self.assertRaises(ValueError):
            scheduler.run()

    def test_single_task(self):
        scheduler = DependencyScheduler(1)

        def task_1():
            return 1

        scheduler.add_task(task_id="A", fn=task_1)
        results = scheduler.run()
        self.assertEqual(results["A"], 1)

    def test_dependency_order(self):
        def task_1(n: int) -> int:
            return n

        def task_2(dependency_results: dict) -> list:
            n = dependency_results["A"]
            squared = [i**2 for i in range(0, n)]
            return squared

        mock_task_2 = MagicMock(wraps=task_2)

        def task_3():
            return "Hello world"

        n = 13

        scheduler = DependencyScheduler(3)
        scheduler.add_task(task_id="B", fn=mock_task_2, depends_on=["A"])
        scheduler.add_task(task_id="A", fn=task_1, n=n)
        scheduler.add_task(task_id="C", fn=task_3)

        results = scheduler.run()

        expected = [i**2 for i in range(0, n)]

        self.assertEqual(results["A"], n)
        self.assertEqual(results["B"], expected)
        mock_task_2.assert_called_once_with(dependency_results={"A": n})

    def test_parallel_independent_tasks(self):

        # events to coordinate and prove simultaenous execution
        started_event_1 = threading.Event()
        started_event_2 = threading.Event()

        release_event = threading.Event()

        def task_1(n: int) -> int:
            started_event_1.set()
            release_event.wait(timeout=2.0)
            return n

        def task_2(dependency_results: dict) -> list:
            n = dependency_results["A"]
            squared = [i**2 for i in range(0, n)]
            return squared

        def task_3():
            started_event_2.set()
            release_event.wait(timeout=2.0)
            return "Hello world"

        # init scheduler
        scheduler = DependencyScheduler(3)
        n = 5
        scheduler.add_task(task_id="A", fn=task_1, n=5)
        scheduler.add_task(task_id="B", fn=task_2, depends_on=["A"])
        scheduler.add_task(task_id="C", fn=task_3)

        # verify final execution results

        with ThreadPoolExecutor(max_workers=3) as executor:
            # run the scheduler in a background thread so we can monitor/control
            future = executor.submit(scheduler.run)

            # assert both tasks started running concurrently
            # this will confirm whether max_workers = 1 or both tasks started concurrently
            try:
                self.assertTrue(started_event_1.wait(timeout=1.0), "Task A failed to start")
                self.assertTrue(started_event_2.wait(timeout=1.0), "Task C failed to start concurrently with task A")
            finally:
                # reease the tasks so that they can complete
                release_event.set()

            # wait for scheduler to finish and fetch the results dictionary safely
            results = future.result(timeout=2.0)

        # verify final execution results

        self.assertEqual(results["A"], n)
        self.assertEqual(results["B"], [i**2 for i in range(0, n)])
        self.assertEqual(results["C"], "Hello world")

    def test_results(self):
        scheduler = DependencyScheduler(max_workers=2)

        scheduler.add_task(task_id="A", fn=pow, args=[2, 3])
        scheduler.add_task(task_id="B", fn=pow, args=[2, 4])

        results = scheduler.run()
        self.assertEqual(results["A"], 8)
        self.assertEqual(results["B"], 16)

    def test_failed_dependency(self):
        def task_1():
            raise ValueError()

        def task_2(depency_results: dict):
            return depency_results["A"] ** 2

        task_2_mock = MagicMock(wraps=task_2)

        def task_3():
            return "Hello world"

        scheduler = DependencyScheduler(max_workers=3)
        scheduler.add_task(task_id="A", fn=task_1)
        scheduler.add_task(task_id="B", fn=task_2_mock, depends_on=["A"])
        scheduler.add_task(task_id="C", fn=task_3)

        with ThreadPoolExecutor(max_workers=3) as executor:
            future = executor.submit(scheduler.run)

            results = future.result()

        task_2_mock.assert_not_called()
        self.assertEqual(len(results), 1)
        self.assertEqual(results["C"], "Hello world")

    def test_cycle_detection(self):
        scheduler = DependencyScheduler(max_workers=3)

        scheduler.add_task(task_id="A", fn=pow, args=[2, 3], depends_on=["B"])
        scheduler.add_task(task_id="B", fn=pow, args=[2, 3], depends_on=["A"])

        with self.assertRaises(DependencyError):
            scheduler.run()

    def test_max_workers(self):
        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()
        release_event = threading.Event()

        def task_1():
            event_1.set()
            release_event.wait(timeout=2.0)
            return "task 1"

        def task_2():
            event_2.set()
            release_event.wait(timeout=2.0)
            return "task 2"

        def task_3():
            event_3.set()
            release_event.wait(timeout=2.0)
            return "task 3"

        scheduler = DependencyScheduler(max_workers=2)
        scheduler.add_task(task_id="A", fn=task_1)
        scheduler.add_task(task_id="B", fn=task_2)
        scheduler.add_task(task_id="C", fn=task_3)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(scheduler.run)

            try:
                self.assertTrue(
                    event_1.wait(timeout=1.0),
                    "Task A failed to start",
                )
                self.assertTrue(
                    event_2.wait(timeout=1.0),
                    "Task B failed to start concurrently with A",
                )
                self.assertFalse(
                    event_3.wait(timeout=0.2),
                    "Task C started while both worker slots were occupied",
                )
            finally:
                release_event.set()

            self.assertTrue(
                event_3.wait(timeout=1.0),
                "Task C failed to start after a worker became available",
            )

            results = future.result(timeout=2.0)

        self.assertEqual(results["A"], "task 1")
        self.assertEqual(results["B"], "task 2")
        self.assertEqual(results["C"], "task 3")

    def test_cancel(self):
        task_started = threading.Event()
        release_task = threading.Event()
        pending_task_executed = threading.Event()

        def running_task():
            task_started.set()
            release_task.wait(timeout=3.0)
            return "completed"

        def pending_task():
            pending_task_executed.set()
            return "should not execute"

        scheduler = DependencyScheduler(max_workers=1)
        scheduler.add_task(task_id="A", fn=running_task)
        scheduler.add_task(task_id="B", fn=pending_task)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future = executor.submit(scheduler.run)

            try:
                self.assertTrue(
                    task_started.wait(timeout=1.0),
                    "Task A failed to start",
                )

                scheduler.cancel(task_id="B")
            finally:
                release_task.set()

            future.result(timeout=4.0)

        self.assertFalse(
            pending_task_executed.is_set(),
            "Task B should not execute after cancellation",
        )
