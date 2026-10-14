from threading import Event

from challenges.challenge_01.challenge_1_10_DependencyScheduler import DependencyScheduler
from unittest import TestCase


def task_1(n: int, completed:Event ) -> list:
    completed.set()
    return [i for i in range(n)]


def task_2(nums: list, completed: Event) -> list:
    primes = []
    for i in nums:
        halfway = i // 2 + 1
        is_prime = True
        for j in range(2, halfway):
            if i % j == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(i)
    completed.set()
    return primes


def task_3(primes: list, completed: Event) -> int:
    """Calculates the ultimate cosmic sum of the discovered primes."""
    completed.set()
    return sum(primes)


def task_4(n: int, completed: Event) -> str:
    """Transforms a number into a rhythmic string chant."""
    completed.set()
    return "-".join(str(i) for i in range(n))


def task_5(sum_val: int, chant: str, completed: Event) -> dict:
    """Merges results from two completely different branches."""
    completed.set()
    return {"cosmic_sum": sum_val, "rhythm": chant, "status": "all_systems_go"}


class TestDependencyScheduler(TestCase):
    def __init__(self, methodName = "runTest"):
        self.completed = Event()
        super().__init__(methodName)
    def test_invalid_max_workers(self):
        with self.assertRaises(ValueError):
            DependencyScheduler(max_workers=0)

        with self.assertRaises(ValueError):
            DependencyScheduler(max_workers=-1)

    def test_add_task(self):
        scheduler = DependencyScheduler(max_workers=3)

        scheduler.add_task(task_id="A", fn=task_1)

        self.assertIn(scheduler.task_ids, "A")

    def test_duplicate_task_id(self):
        scheduler = DependencyScheduler(max_workers=3)
        scheduler.add_task(task_id="A", fn=task_1, n=10)
        scheduler.add_task(task_id="B", fn=task_2)

        with self.assertRaises(ValueError):
            scheduler.add_task(task_id="A", fn=task_1, n=10)

    def test_missing_dependency(self):
        scheduler = DependencyScheduler(max_workers=3)
        scheduler.add_task(task_id="A", fn=task_1)

        with self.assertRaises(ValueError):

            scheduler.add_task(task_id="B", fn=task_2, depends_on=["C"])

    def test_single_task(self):
        scheduler = DependencyScheduler(max_workers=1)
        scheduler.add_task(task_id="A", fn=task_1, n=10)

        expected = {"A": [i for i in range(10)]}
        result = scheduler.run()

        self.assertEqual(result, expected)

    def test_dependency_order(self):
        scheduler = DependencyScheduler(5)
        scheduler.add_task(task_id=1, fn=task_1, n=50, depends_on=None)
        results = scheduler.run()
        scheduler.add_task(task_id=2, fn=task_2, nums=results["1"], depends_on=1)
        scheduler.add_task(task_id=3, fn=task_3, depends_on=1

                           
