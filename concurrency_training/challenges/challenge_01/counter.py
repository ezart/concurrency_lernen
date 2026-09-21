import threading




class UnsafeCounter:
    def __init__(self):
        self.count = 0
    def increment(self) -> None:
        self.count += 1
    def value(self)->int:
        return self.count


class SafeCounter:
    _data_lock = threading.Lock()

    def __init__(self):
        self.count = 0
    def increment(self)->None:
        with SafeCounter._data_lock:
            self.count += 1
    def value(self)->int:
        with SafeCounter._data_lock:
            return self.count

class InstanceSafeCounter:

    def __init__(self):
        self.counter = 0
        self._data_lock = threading.Lock()

    def increment(self)->None:
        with self._data_lock:
            self.counter += 1
    def value(self)->int:
        with self._data_lock:
            return self.counter

    1
class AtomicConditionalCounter:
    

    def __init__(self):
        self.counter = 0
        self.data_lock = threading.Lock()
        

    def increment(self)->None:
            with self.data_lock:
                self.counter += 1
        
    def increment_if_below(self,limit:int)->bool:
        if limit <= 0:
            return False
        with self.data_lock:
            if self.counter < limit:
                self.counter += 1
                return True
            else:
                return False

    def value(self):
        with self.data_lock:
            return self.counter
            
