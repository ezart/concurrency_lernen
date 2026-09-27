from multiprocessing import Process

from challenges.challenge_01.parallel_counter import ParallelCounter

import unittest


class TestParallelCounter(unittest.TestCase):
    def test_initial_value_is_respected(self):
        counter = ParallelCounter(initial_value=30)
        expected_value = 30
        self.assertEqual(counter.counter, expected_value)

    def test_single_proces_can_increment_counter(self):
        def worker(counter, lock, amount):
            with lock:
                counter += amount

        pc = ParallelCounter(initial_value=10)

        p = Process(target=worker, args=(pc.counter, pc.lock, 10))

        #  start the process
        p.start()
        #  wait for process to finish
        p.join()

        self.assertEqual(pc.counter, 20)
