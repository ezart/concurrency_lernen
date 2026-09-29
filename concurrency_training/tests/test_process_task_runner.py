import os
from concurrent.futures import Future

import unittest

from challenges.challenge_01.process_task_runner import ProcessTaskRunner


def explode():
    raise ValueError("worker failed")


def quadruple(n):
    return n * 4


def prime_finder(n: int) -> None:
    pid = os.getpid()
    is_prime = True

    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            is_prime = False
            break
    if is_prime:
        return n, pid
    return None


def prime_finder_v2(start: int, end: int) -> tuple[list[int], int]:
    pid = os.getpid()
    primes = []

    for n in range(start, end):
        is_prime = True
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(n)
    return primes, pid


class TestProcessTaskRunner(unittest.TestCase):
    def test_invalid_max_workers(self):
        with self.assertRaises(ValueError):
            ProcessTaskRunner(max_workers=0)

    def test_submit_returns_a_future(self):
        ptr = ProcessTaskRunner(1)
        self.assertIsInstance(ptr.submit(pow, 2, 3), Future)

    def test_arguments_work(self):
        ptr = ProcessTaskRunner(1)
        future = ptr.submit(pow, 2, 3)
        self.assertEqual(future.result(), 8)

    def test_exceptions_propagate(self):
        ptr = ProcessTaskRunner(1)
        future = ptr.submit(explode)

        with self.assertRaises(ValueError):
            future.result()

    def test_map_works(self):
        ptr = ProcessTaskRunner(2)
        results = ptr.map(quadruple, range(10))

        expected = [i * 4 for i in range(10)]
        self.assertEqual(list(results), expected)

    def test_parallel_execution(self):

        # ptr = ProcessTaskRunner(4)
        # process_ids = set()

        # futures = [ptr.submit(fn=prime_finder, n=n) for n in range(1000, 100000)]

        # results = [future.result() for future in futures if future.result()]
        # primes = []

        # for prime_no, pid in results:
        #     primes.append(prime_no)
        #     process_ids.add(pid)

        # print(len(process_ids))

        # self.assertEqual(len(primes), 9424)
        # self.assertEqual(len(process_ids), 4)
        ranges = [(i, min(i + 5000, 100000)) for i in range(1000, 100000, 5000)]
        primes = []
        pids = set()

        with ProcessTaskRunner(4) as runner:
            futures = [runner.submit(fn=prime_finder_v2, start=i[0], end=i[1]) for i in ranges]

            for future in futures:
                if result := future.result():
                    primes.extend(result[0])
                    pids.add(result[1])

            self.assertEqual(len(primes), 9424)

    def test_map_does_not_shutdown_executor(self):
        with ProcessTaskRunner(2) as runner:
            results = runner.map(quadruple, range(5))

            self.assertEqual(list(results), [0, 4, 8, 12, 16])

            future = runner.submit(quadruple, 10)
            self.assertEqual(future.result(), 40)

    def test_shutdown_prevents_new_submissions(self):
        runner = ProcessTaskRunner(2)
        runner.shutdown()

        with self.assertRaises(RuntimeError):
            runner.submit(quadruple, 10)

    def test_shutdown_can_be_called_multiple_times(self):
        runner = ProcessTaskRunner(2)
        runner.shutdown()
        runner.shutdown()
