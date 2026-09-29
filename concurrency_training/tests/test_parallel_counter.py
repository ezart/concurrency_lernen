from multiprocessing import Process

from challenges.challenge_01.parallel_counter import ParallelCounter

import unittest


def worker(pc: ParallelCounter, amount: int):
    for _ in range(10000):
        pc.increment(amount)


class TestParallelCounter(unittest.TestCase):
    def test_initial_value_is_respected(self):
        counter = ParallelCounter(initial_value=30)
        expected_value = 30
        self.assertEqual(counter.value(), expected_value)

    def test_single_proces_can_increment_counter(self):

        pc = ParallelCounter(initial_value=0)

        p = Process(target=worker, args=(pc, 10))

        #  start the process
        p.start()
        #  wait for process to finish
        p.join(timeout=1.0)
        self.assertFalse(p.is_alive())
        self.assertEqual(p.exitcode, 0)

        expected_value = 100000

        self.assertEqual(pc.value(), expected_value)

    def test_multiple_processess_increment(self):
        pc = ParallelCounter(initial_value=0)
        processes = [Process(target=worker, args=(pc, 10)) for _ in range(10)]

        for process in processes:
            process.start()

        for process in processes:
            process.join()

        expected_value = 1000000
        self.assertEqual(pc.value(), expected_value)
        self.assertTrue(all([p.exitcode == 0 for p in processes]))

    def test_negative_increment(self):
        pc = ParallelCounter(initial_value=50)

        pc.increment(-10)

        self.assertEqual(pc.value(), 40)
