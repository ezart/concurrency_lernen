from collections import deque
import threading


class BoundedQueue:
    """
    - capacity> 0
    - put:
      adds an item
      if the queue is full, the calling thread waits

    - get:
      removes and returns an item
      if queue is empty, the calling thread waits

    multiple producers and consumers must be supported
    no busy waiting
    use threading.condition
    put() and get() must be safe under concurrent access
    the queue must never exceed its capacity
    items must come out in FIFO order
    """
    def __init__(self,capacity:int):
        self.queue = deque()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        if capacity <= 0:
            raise ValueError("capacity should be more than 0")
        self.capacity = capacity
        
    def put(self, item):
        with self.condition:
            while self.capacity <= len(self.queue):
                self.condition.wait()
            self.queue.append(item)
            self.condition.notify_all()
                

    def get(self):
        with self.condition:
            while not self.queue:
                self.condition.wait()
            item =self.queue.popleft()
            self.condition.notify_all()
            return item
