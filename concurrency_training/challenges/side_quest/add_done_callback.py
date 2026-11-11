from concurrent.futures import ThreadPoolExecutor, Future
from threading import Event
from unittest.mock import MagicMock

event = Event()
is_started = Event()
callback_event = Event()

# Shared container for the callback's processed result
callback_results = {}


def task_1():
    is_started.set()
    event.wait()
    return "Hello"


def task_2(future: Future):
    try:
        # 1. Retrieve the original task's result
        result = future.result(timeout=1.0)

        # 2. Transform and store the result
        callback_results["message"] = f"{result} world"
    finally:
        # 3. Signal that callback processing has ended
        callback_event.set()


mock_task_2 = MagicMock(wraps=task_2)

with ThreadPoolExecutor(max_workers=1) as executor:
    try:
        future = executor.submit(task_1)
        future.add_done_callback(mock_task_2)

        assert is_started.wait(timeout=1.0)

        # Release the original task
        event.set()

        assert future.result(timeout=1.0) == "Hello"
        assert future.done()

        # 4. Wait for callback processing
        assert callback_event.wait(timeout=1.0)

        # Verify the transformed value
        assert callback_results["message"] == "Hello world"

        # Verify callback invocation
        mock_task_2.assert_called_once_with(future)

    finally:
        event.set()
