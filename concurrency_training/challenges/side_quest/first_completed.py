from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Event

event_a = Event()
event_b = Event()
starting_event_a = Event()
starting_event_b = Event()


def task_a():
    starting_event_a.set()
    event_a.wait()
    return "task a complete"


def task_b():
    starting_event_b.set()
    event_b.wait()
    return "task b complete"


with ThreadPoolExecutor(max_workers=2) as executor:

    # release task A
    try:
        # start both tasks
        future_1 = executor.submit(task_a)
        future_2 = executor.submit(task_b)

        # assert both events started
        assert starting_event_a.wait(timeout=1.0)
        assert starting_event_b.wait(timeout=1.0)
        event_a.set()

        # blocks until the first task is completed, cancelled or failed
        done, not_done = wait([future_1, future_2], timeout=1.0, return_when=FIRST_COMPLETED)
        # breakpoint()
        assert future_1.done() == True
        assert future_2.done() == False

        assert future_1 in done
        assert future_2 in not_done

        # release B
        event_b.set()

        # Verify both tasks completed successfully
        assert future_1.result(timeout=1.0) == "task a complete"
        assert future_2.result(timeout=1.0) == "task b complete"

        # Verify both futures are completed
        assert future_1.done()
        assert future_2.done()

    finally:
        event_a.set()
        event_b.set()
