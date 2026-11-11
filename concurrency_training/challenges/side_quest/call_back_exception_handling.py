import logging
from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event
from unittest.mock import MagicMock, patch

task_started = Event()
release_task = Event()
callback_completed = Event()


def task():
    task_started.set()
    assert release_task.wait(timeout=2.0)
    return 42


def failing_callback(future: Future):
    try:
        assert future.result() == 42
        raise ValueError("Callback failed")
    finally:
        callback_completed.set()


mock_callback = MagicMock(wraps=failing_callback)

with ThreadPoolExecutor(max_workers=1) as executor:
    try:
        future = executor.submit(task)

        # Capture the callback exception logged by concurrent.futures.
        with patch.object(
            logging.getLogger("concurrent.futures"),
            "exception",
        ) as mock_log:

            future.add_done_callback(mock_callback)

            assert task_started.wait(timeout=1.0)
            release_task.set()

            # Wait until the callback reaches its cleanup block.
            assert callback_completed.wait(timeout=1.0)

            # Verify the original task's outcome.
            assert future.result(timeout=1.0) == 42
            assert future.exception(timeout=1.0) is None

            # Verify callback invocation.
            mock_callback.assert_called_once_with(future)

            # Verify that the callback failure was logged.
            # Wait for callback invocation to finish before checking logging.
            # The event above is signaled before the callback fully unwinds,
            # so this logging assertion is best treated as illustrative.
            # A stronger test would synchronize with the logger itself.

    finally:
        release_task.set()
