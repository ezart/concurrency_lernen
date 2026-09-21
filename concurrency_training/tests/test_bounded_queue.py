import threading
from concurrent.futures import ThreadPoolExecutor
import unittest

from  challenges.challenge_01.bounded_queue import BoundedQueue


class BoundedQueueTest(unittest.TestCase):
    """
    test_producer_blocks_when_full
    test_multiple_producers_and_consumers
    """
    def test_put_and_get(self):
        q = BoundedQueue(capacity=3)
        q.put(2)
        self.assertEqual(q.get(),2)

    def test_fifo_order(self):
        q = BoundedQueue(capacity=3)
        q.put(1)
        q.put(2)
        q.put(3)

        self.assertEqual(q.get(),1)

    def test_capacity(self):
        
        q1 = BoundedQueue(2)
        self.assertEqual(q1.capacity,2)
        q1.put(2)
        q1.put(2)
        q1.get()
        q1.put(4)

        self.assertEqual(len(q1.queue),2)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            q = BoundedQueue(0)

    def test_producer_blocks_when_full(self):
        q = BoundedQueue(capacity=5)

        for i in range(5):
            q.put(i)


        def producer_worker():
            q.put(6)
            q.put(27)

        def consumer_worker():
            q.get()
            q.get()
        

        thread1 = threading.Thread(target=producer_worker)
        thread2 = threading.Thread(target=consumer_worker)

        # Start producer; it should immediately block trying to put 6
        thread1.start()

        # let thread1 run for a moment and blcok
        thread1.join(timeout=0.1)

        # confirm thread1 is stuck waiting for space in the queue
        self.assertTrue(thread1.is_alive())
        # start thread2 to unblock the producer
        thread2.start()

        # both threads should now finish cleanly
        thread1.join(timeout=1.0)
        thread2.join(timeout=1.0)
        self.assertFalse(thread1.is_alive(), "Producer thread should finish after consumer reads items")
        self.assertFalse(thread2.is_alive(), "Consumer thread should finish")
        self.assertEqual(q.queue[-1],27)



    def test_multiple_producers_consumers(self):
        """
        create z queue
        create shared/producted consumed tracking
        create 3 producers
            each produces 100 items
        create 3 consumers
            each consumes 100 items
        
        start all six workers concurrently
        wait for all six to finish

        Assert:
            300 produced
            300 consumed
            no duplicates
            produced == consumed
        """
        q = BoundedQueue(capacity=5)

        produced =[]
        consumed = []

        lock = threading.Lock()
        generator_lock = threading.Lock()

        def unique_items_generator():
                    for i in range(0,300):
                            yield i

        unique_item = unique_items_generator()

        def producer_worker():
            for _ in range(0,100):
                # protect the next operation not the yield
                with generator_lock:
                    item = next(unique_item)
                with lock:
                    produced.append(item)
                q.put(item)



        def consumer_worker():
            for _ in range(0,100):
                item = q.get()

                with lock:
                    consumed.append(item)
             
    

        with ThreadPoolExecutor() as executor:

            futures =[
                executor.submit(producer_worker),
                executor.submit(producer_worker),
                executor.submit(producer_worker),
                executor.submit(consumer_worker),
                executor.submit(consumer_worker),
                executor.submit(consumer_worker)
            ]

            for future in futures:
                future.result()



            


        self.assertEqual(len(produced),len(consumed))
        self.assertEqual(len(produced),300)
        self.assertEqual(len(set(consumed)),300)
        self.assertEqual(len(set(produced)),300)
        self.assertTrue(set(consumed) == set(produced))











        
        
       

    

    


