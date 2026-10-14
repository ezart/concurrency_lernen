from concurrent.futures import Future
import threading

from challenges.challenge_01.challenge_1_9_task_coordinator import TaskCoordinator

import unittest


def make_task(
    task_id,
    events: dict,
    wait_for_task=None,
):
    def task_func():
        if wait_for_task:
            events[wait_for_task].wait()
        events[task_id].set()
        print(f"task running ", task_id)
        if task_id == "F":
            events[task_id].set()
            raise ValueError()

        # print(f"task {task_id} set")
        return task_id

    return task_func


class TaskCoordinatorTest(unittest.TestCase):
    def test_invalid_max_workers(self):
        with self.assertRaises(ValueError):
            TaskCoordinator(0)

    def test_submit_returns_future(self):
        with TaskCoordinator(2) as coordinator:
            future = coordinator.submit(pow, 2, 3)

            self.assertIsInstance(future, Future)

    def test_collect(self):
        events = {i: threading.Event() for i in ["A", "B", "C", "D"]}
        coordinator = TaskCoordinator(max_workers=4)
        with coordinator as c:
            c.submit(make_task(task_id="D", wait_for_task="A", events=events))
            c.submit(make_task(task_id="B", wait_for_task="D", events=events))
            c.submit(make_task(task_id="C", wait_for_task="B", events=events))
            c.submit(make_task(task_id="A", wait_for_task=None, events=events))

            events["A"].set()

            self.assertEqual([i[1] for i in coordinator.collect()], ["A", "D", "B", "C"])

    def test_collect_with_failed_task(self):
        events = {i: threading.Event() for i in ["A", "B", "C", "D", "F"]}
        coordinator = TaskCoordinator(max_workers=4)
        with coordinator as c:

            c.submit(make_task(task_id="D", wait_for_task="A", events=events))
            c.submit(make_task(task_id="B", wait_for_task="D", events=events))
            c.submit(make_task(task_id="F", wait_for_task="B", events=events))
            c.submit(make_task(task_id="C", wait_for_task="F", events=events))
            c.submit(make_task(task_id="A", wait_for_task=None, events=events))

            events["A"].set()

            results = c.collect()

            self.assertEqual(results[0], ("ok", "A"))
            self.assertEqual(results[1], ("ok", "D"))
            self.assertEqual(results[2], ("ok", "B"))
            self.assertEqual(results[3][0], "error")
            self.assertIs(results[3][1], ValueError)
            self.assertEqual(results[4], ("ok", "C"))
