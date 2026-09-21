
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest


from challenges.challenge_01.counter import (
    SafeCounter,
    UnsafeCounter,
    InstanceSafeCounter,
    AtomicConditionalCounter
)


class TestUnsafeCounter(unittest.TestCase):
    def test_initial_value_is_zero(self):
        counter = UnsafeCounter()

        self.assertEqual(counter.value(), 0)

    def test_increment_increases_value(self):
        counter = UnsafeCounter()

        counter.increment()

        self.assertEqual(counter.value(), 1)

    def test_sequential_increments(self):
        counter = UnsafeCounter()

        for _ in range(100):
            counter.increment()

        self.assertEqual(counter.value(), 100)


class TestSafeCounter(unittest.TestCase):
    def test_initial_value_is_zero(self):
        counter = SafeCounter()

        self.assertEqual(counter.value(), 0)

    def test_increment_increases_value(self):
        counter = SafeCounter()

        counter.increment()

        self.assertEqual(counter.value(), 1)

    def test_sequential_increments(self):
        counter = SafeCounter()

        for _ in range(100):
            counter.increment()

        self.assertEqual(counter.value(), 100)

    def test_concurrent_increments(self):
        counter = SafeCounter()

        number_of_threads = 10
        increments_per_thread = 1_000

        threads = [
            threading.Thread(
                target=lambda: [
                    counter.increment()
                    for _ in range(increments_per_thread)
                ]
            )
            for _ in range(number_of_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        expected = number_of_threads * increments_per_thread

        self.assertEqual(counter.value(), expected)



class TestInstanceSafeCounter(unittest.TestCase):
    def test_initial_value_is_zero(self):
        counter = InstanceSafeCounter()
        self.assertEqual(counter.value(),0)


    def test_increment_increases_value(self):
            counter = InstanceSafeCounter()
    
            counter.increment()
    
            self.assertEqual(counter.value(), 1)
    
    def test_sequential_increments(self):
        counter = InstanceSafeCounter()

        for _ in range(100):
            counter.increment()

        self.assertEqual(counter.value(), 100)

    def test_concurrent_increments(self):
        counter = InstanceSafeCounter()

        number_of_threads = 10
        increments_per_thread = 1_000

        threads = [
            threading.Thread(
                target=lambda: [
                    counter.increment()
                    for _ in range(increments_per_thread)
                ]
            )
            for _ in range(number_of_threads)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        expected = number_of_threads * increments_per_thread

        self.assertEqual(counter.value(), expected)

    def test_independent_counters(self):
        counter1 = InstanceSafeCounter()
        counter2 = InstanceSafeCounter()

        for i in range(5):
            counter1.increment()

        for l in range(10):
            counter2.increment()

        self.assertNotEqual(counter1.value(), counter2.value())
        self.assertEqual(counter1.value(),5)
        self.assertEqual(counter2.value(),10)

    def test_concurrent_independent_counters(self):
        counter1 = InstanceSafeCounter()
        counter2 = InstanceSafeCounter()

        no_of_threads = 10
        increments_per_thread = 1_000

        def thread_worker():
            counter1.increment()
            counter2.increment()

        threads = [
            threading.Thread(
                target=lambda:
                [thread_worker() for _ in range(increments_per_thread)
                ]
            ) 
        for _ in range(no_of_threads)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(counter1.value(), counter2.value())


class TestAtomicConditionalCounter(unittest.TestCase):
    def test_initial_value_is_zero(self):
            counter = AtomicConditionalCounter()
    
            self.assertEqual(counter.value(), 0)
    
    def test_increment_increases_value(self):
        counter = AtomicConditionalCounter()

        counter.increment()

        self.assertEqual(counter.value(), 1)

    def test_sequential_increments(self):
        counter = AtomicConditionalCounter()

        for _ in range(100):
            counter.increment()

        self.assertEqual(counter.value(), 100)

    def test_increment_if_below(self):
        counter = AtomicConditionalCounter()
        no_of_threads = 10
        futures =[]

        with ThreadPoolExecutor() as executor:
            for _ in range(no_of_threads):
                future = executor.submit(counter.increment_if_below, 5)
                futures.append(future)
        results =[future.result() for future in futures]
        self.assertEqual(len([x for x in results if x is True]),5)
        self.assertEqual(len([x for x in results if x is False]),5)
        self.assertEqual(counter.value(),5)

    def test_increment_if_limit_0(self):
        counter = AtomicConditionalCounter()
        self.assertFalse(counter.increment_if_below(0))
        self.assertEqual(counter.value(),0)
    def test_increment_if_limit_negative_1(self):
        counter = AtomicConditionalCounter()
        self.assertFalse(counter.increment_if_below(-1))
        self.assertEqual(counter.value(),0)

    def test_concurrent_calls_limit_1(self):
        counter = AtomicConditionalCounter()
        futures = []
        with ThreadPoolExecutor() as executor:
            for _ in range(5):
                futures.append(executor.submit(counter.increment_if_below,1))

        results = [future.result() for future in futures]
        self.assertEqual(results.count(True),1)
        self.assertEqual(results.count(False),4)
        self.assertEqual(counter.value(),1)

    def test_independent_counters(self):
        counter = AtomicConditionalCounter()
        counter2 = AtomicConditionalCounter()
        with ThreadPoolExecutor() as executor:
            for _ in range(5):
                executor.submit(counter.increment_if_below,10)
            for _ in range(10):
                executor.submit(counter2.increment_if_below,10)

        self.assertNotEqual(counter.value(), counter2.value())
        self.assertEqual(counter.value(),5)
        self.assertEqual(counter2.value(),10)
            

        


                         
                         

    




